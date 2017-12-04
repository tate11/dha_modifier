# -*- coding: utf-8 -*-

import logging
import time
import xmlrpclib

from odoo import models, fields, api
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.modules.module import get_module_resource
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.hr_zkteco_machine.zklib import zklib
from odoo.addons.hr_zkteco_machine.zklib import zkconst

_logger = logging.getLogger(__name__)


# inherit hr_employee module
class hr_employee(models.Model):
    _inherit = 'hr.employee'

    emp_code = fields.Char("Emp Code")
    category = fields.Char("Category")


# inherit hr_attendance module
class hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    emp_code = fields.Char("Emp Code")

    # # overriding the __check_validity fucntion to not check the "check_out" value for employee attendance
    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     """ Verifies the validity of the attendance record compared to the others from the same employee.
    #         For the same employee we must have :
    #             * maximum 1 "open" attendance record (without check_out)
    #             * no overlapping time slices with previous employee records
    #     """
    #     for attendance in self:
    #         # we take the latest attendance before our check_in time and check it doesn't overlap with ours
    #         last_attendance_before_check_in = self.env['hr.attendance'].search([
    #             ('employee_id', '=', attendance.employee_id.id),
    #             ('check_in', '<=', attendance.check_in),
    #             ('id', '!=', attendance.id),
    #         ], order='check_in desc', limit=1)
    #         if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out >= attendance.check_in:
    #             raise ValidationError(_(
    #                 "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                                       'empl_name': attendance.employee_id.name_related,
    #                                       'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self,
    #                                                                                                               fields.Datetime.from_string(
    #                                                                                                                   attendance.check_in))),
    #                                   })
    #
    #         # Commented out the attendance.checkout checking
    #         if not attendance.check_out:
    #             # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
    #             no_check_out_attendances = self.env['hr.attendance'].search([
    #                 ('employee_id', '=', attendance.employee_id.id),
    #                 ('check_out', '=', False),
    #                 ('id', '!=', attendance.id),
    #             ])
    #             if no_check_out_attendances:
    #                 pass
    #                 # raise ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
    #                 #    'empl_name': attendance.employee_id.name_related,
    #                 #    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
    #                 # })
    #         else:
    #             # we verify that the latest attendance with check_in time before our check_out time
    #             # is the same as the one before our check_in time computed before, otherwise it overlaps
    #             last_attendance_before_check_out = self.env['hr.attendance'].search([
    #                 ('employee_id', '=', attendance.employee_id.id),
    #                 ('check_in', '<=', attendance.check_out),
    #                 ('id', '!=', attendance.id),
    #             ], order='check_in desc', limit=1)
    #             if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
    #                 raise ValidationError(_(
    #                     "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                                           'empl_name': attendance.employee_id.name_related,
    #                                           'datetime': fields.Datetime.to_string(
    #                                               fields.Datetime.context_timestamp(self, fields.Datetime.from_string(
    #                                                   last_attendance_before_check_out.check_in))),
    #                                       })


# biometric machine module
class biometric_machine(models.Model):
    _name = 'biometric.machine'

    name = fields.Char("Machine IP")
    ref_name = fields.Char("Location")
    port = fields.Integer("Port Number")
    address_id = fields.Many2one('res.partner', string='Partner')
    # Multi-company
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id)
    type = fields.Selection([('local','Local'),('remote','Remote')], 'Type', default='remote')
    odoo_url = fields.Char('Local Odoo Url')
    db_name = fields.Char('DB Name')
    user = fields.Char('DB User')
    pwd = fields.Char('DB Password')

    # function to download attendance
    @api.multi
    def download_attendance(self):
        hr_attendance = self.env['hr.attendance'].browse()
        for info in self:
            machine_ip = info.name
            port = info.port

            # connect to the biometric device using the machine ip and port
            zk = zklib.ZKLib(machine_ip, int(port))
            res = zk.connect()
            if res:
                zk.enableDevice()
                user = zk.getUser()
                attendance = zk.getAttendance()
                if (attendance):
                    # get the user data from the biometric device
                    user = zk.getUser()
                    for lattendance in attendance:
                        time_att = str(lattendance[2].date()) + ' ' + str(lattendance[2].time())
                        atten_time = datetime.strptime(str(time_att), '%Y-%m-%d %H:%M:%S')
                        atten_time = datetime.strftime(atten_time, '%Y-%m-%d %I:%M:%S')
                        in_time = datetime.strptime(atten_time, '%Y-%m-%d %H:%M:%S').time()
                        time_new = str(in_time)
                        time_new = time_new.replace(":", ".", 1)
                        time_new = time_new[0:5]
                        check_in = fields.Datetime.to_string(
                            fields.Datetime.context_timestamp(self, fields.Datetime.from_string(atten_time))),
                        if user:
                            for uid in user:
                                # compare the employee code in user data with employee code in attendance data of each employee in the attendance list
                                # only matched users are processed
                                if user[uid][0] == str(lattendance[0]):
                                    get_user_id = self.env['hr.employee'].search(
                                        [('emp_code', '=', str(lattendance[0]))])
                                    if get_user_id:

                                        # check for duplicate attendance values
                                        duplicate_atten_ids = self.env['hr.attendance'].search(
                                            [('emp_code', '=', str(lattendance[0])), ('check_in', '=', check_in)])
                                        if duplicate_atten_ids:
                                            continue
                                        else:
                                            # create attendance values to hr.attendance table
                                            search_user_id = self.env['hr.employee'].search(
                                                [('name', '=', user[uid][1]), ('emp_code', '=', str(lattendance[0]))])
                                            if search_user_id:
                                                data = hr_attendance.create(
                                                    {'employee_id': get_user_id.id, 'emp_code': lattendance[0],
                                                     'check_in': check_in})
                                    else:
                                        # employee = self.env['hr.employee'].create(
                                        #     {'emp_code': str(lattendance[0]), 'name': user[uid][1]})
                                        # data = hr_attendance.create(
                                        #     {'employee_id': employee.id, 'emp_code': lattendance[0],
                                        #      'check_in': check_in})
                                        _logger.warning(
                                            _('Have no employee for ID: %s.' % (str(lattendance[0]))))
                                else:
                                    pass

                    zk.enableDevice()
                    zk.disconnect()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    @api.model
    def get_all_attendance(self, ip, port, ref_name):
        result = []
        _logger.warning("Start get attendance at %s" % (ref_name or ip))
        machine_ip = ip
        port = port

        # connect to the biometric device using the machine ip and port
        zk = zklib.ZKLib(machine_ip, int(port))
        res = zk.connect()
        if res:
            zk.enableDevice()
            attendance = zk.getAttendance()
            if (attendance):
                zk.enableDevice()
                zk.disconnect()
                result.append(attendance)
            else:
                _logger.warning(_('Unable to get the attendance log from %s, please try again later.' % (
                ref_name or ip)))
        else:
            _logger.warning(_('Unable to connect to %s, please check the parameters and network connections.' % (
            ref_name or ip)))
        return result

    @api.model
    def parse_attendance(self, attendances):
        Attendance = self.env['hr.attendance']
        for attendance in attendances:
            if (attendance):
                for lattendance in attendance:
                    time_att = datetime.strptime(lattendance[2].value, '%Y%m%dT%H:%M:%S')
                    time_att = time_att - timedelta(hours=7)
                    check_in = time_att.strftime('%Y-%m-%d %H:%M:%S')

                    # compare the employee code in user data with employee code in attendance data of each employee in the attendance list
                    # only matched users are processed
                    get_user_id = self.env['hr.employee'].search(
                        [('emp_code', '=', str(lattendance[0]))])
                    if get_user_id:

                        # check for duplicate attendance values
                        duplicate_atten_ids = self.env['hr.attendance'].search(
                            [('emp_code', '=', str(lattendance[0])), '|',('check_in', '=', check_in), ('check_out', '=', check_in)])
                        if duplicate_atten_ids:
                            continue
                        if duplicate_atten_ids:
                            continue
                        check = self.check_att_time(check_in)
                        if not check:
                            # create attendance values to hr.attendance table
                            data = Attendance.create(
                                {'employee_id': get_user_id.id, 'emp_code': lattendance[0],
                                 'check_in': check_in})
                    else:
                        _logger.warning(
                            _('Have no employee for ID: %s.' %(str(lattendance[0]))))
        return True

    @api.model
    def check_att_time(self, att_time):
        # param: att_time : datetime string format
        data = []
        Attendance = self.env['hr.attendance']
        now_date = datetime.now().date()
        date_start = now_date.strftime('%Y-%m-%d 00:00:00')
        date_end = (now_date + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        attendance = Attendance.search([('check_in','>=', date_start), '|',('check_out','<', date_end),('check_out','=', False)], limit=1)
        if not attendance:
            return False
        att_time = datetime.strptime(att_time, DEFAULT_SERVER_DATETIME_FORMAT)

        attendance_in = attendance.check_in
        attendance_out = attendance.check_out
        if attendance_in:
            attendance_in = datetime.strptime(attendance_in, DEFAULT_SERVER_DATETIME_FORMAT)
        if attendance_out:
            attendance_out = datetime.strptime(attendance_out, DEFAULT_SERVER_DATETIME_FORMAT)

        if attendance_in and att_time < attendance_in:
            if not attendance_out:
                data['check_out'] = attendance.check_in
            data['check_in'] = att_time
        elif attendance_in and att_time < attendance_in and (att_time > attendance_out or not attendance_out):
            data['check_out'] = att_time
        attendance.write(data)
        if data:
            return True
        return False

    # Dowload attendence data regularly
    @api.model
    def schedule_download(self):
        records = self.search([])
        for record in records:
            try:
                if record.type == 'remote':
                    res = records.filtered(lambda r: r.type == 'remote').schedule_get_attendance_from_sub()
                else:
                    res = records.filtered(lambda r: r.type == 'local').download_attendance()
            except:
                _logger.warning(
                    _('Machine is not connected: %s.' % (record.ref_name or record.name)))
        return True

    @api.model
    def schedule_get_attendance_from_sub(self):
        for record in self:
            attendances = False
            try:
                attendances = record.xmlprc_get_attendance()
            except:
                _logger.warning(
                    _("Can't connect to: %s." % (record.ref_name or record.name)))
            if attendances:
                self.parse_attendance(attendances)

    @api.model
    def xmlprc_get_attendance(self):
        HOST = self.odoo_url
        PORT = 80
        DB = self.db_name
        USER = self.user
        PASS = self.pwd

        root = '%s/xmlrpc/'%(HOST)

        uid = xmlrpclib.ServerProxy(root + 'common').login(DB, USER, PASS)

        # Create a new note
        sock = xmlrpclib.ServerProxy(root + '2/object')
        res = sock.execute_kw(DB, uid, PASS, 'biometric.machine', 'get_all_attendance', [self.name or '', self.port or '', self.ref_name or ''], {})
        return res

