# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, config
import StringIO
from collections import deque
import os
import uuid

try:
        import xlwt
except ImportError:
    xlwt = None

class dhac_calendar_export(models.TransientModel):
    _name = 'dhac.calendar.export'

    name = fields.Char('Name')
    time_start = fields.Datetime('From')
    time_end = fields.Datetime('To')
    attendees = fields.Many2many('calendar.export.attendees', 'export_calendar_export_calendar_attendees_rel', 'id1',
                                 'id2', 'Attendees Template')
    partner_ids = fields.Many2many('res.partner', 'export_calendar_res_partner_rel', 'id1', 'id2', 'Attendees')

    @api.onchange('attendees')
    def onchange_attendees(self):
        self.partner_ids = False
        for att in self.attendees:
            self.partner_ids += att.partner_ids

    @api.multi
    def do_action(self):
        Calendar = self.env['calendar.event']
        calendar_ids = Calendar.sudo().with_context({'virtual_id': True}).search(
            [('start', '>=', self.time_start), ('stop', '<=', self.time_end),
             ('partner_ids', 'in', self.partner_ids.ids)], order='start_datetime')
        # calendar_ids = calendar_ids.filtered(lambda r: r.start_datetime >= self.time_start and r.stop_datetime <= self.time_end)
        if not calendar_ids:
            raise UserError(_('Have no Calendar found.'))
        data = []
        for cal in calendar_ids:
            start = (
            datetime.strptime(cal.start, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=7)).strftime(
                '%d/%m/%Y %H:%M:%S')
            end = (datetime.strptime(cal.stop, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=7)).strftime(
                '%d/%m/%Y %H:%M:%S')
            attendees_name = ''
            for att in cal.partner_ids:
                if attendees_name == '':
                    attendees_name += att.name or ''
                else:
                    attendees_name += '\n' + att.name or ''
            data.append((start, end, cal.name, attendees_name, cal.location or ''))
        attachment_id = self.export_data(data)
        if attachment_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return {
                'type': 'ir.actions.act_url',
                'name': "Download Calender Report File",
                'target': 'new',
                'url': base_url + "/web/content/%s?download=1" % (attachment_id),
            }

    @api.model
    def export_data(self, datas):
        if not datas or datas == []:
            return False
        else:
            workbook = xlwt.Workbook(encoding='UTF-8')
            header_plain = xlwt.easyxf("align: vert centre, horz center, wrap yes;")
            col_plain = xlwt.easyxf("align: vert centre, horz center, wrap yes;")
            worksheet = workbook.add_sheet('Calendar')

            worksheet.write(0, 0, 'From', header_plain)
            worksheet.write(0, 1, 'To', header_plain)
            worksheet.write(0, 2, 'Subject', header_plain)
            worksheet.write(0, 3, 'Attendees', header_plain)
            worksheet.write(0, 4, 'Location', header_plain)

            for count in range(0, 5):
                worksheet.col(count).width = 8000

            row = 1
            for data in datas:
                col = 0
                for res in data:
                    worksheet.write(row, col, res, col_plain)
                    col += 1
                row += 1
            today = date.today()
            filepath = self.get_tmp_path('%s-%s-export-calendar-data.xls' % (today.strftime('%y-%m-%d'), uuid.uuid4(),))
            workbook.save(filepath)
            att_id = self.create_odoo_attachment(filepath)
            return att_id

    @api.model
    def create_odoo_attachment(self, excel_path, filename=False):
        excel_data = ''
        now = datetime.now()
        with open(excel_path, 'r') as file:  # Use file to refer to the file object
            data = file.read()
            excel_data += data
        if not filename:
            filename = 'calendar_report-%s-%s-%s.xls'%(str(now.day),str(now.month),str(now.year))
        attachment = self.env.get('ir.attachment').create({
            'name': filename,
            'res_name': filename,
            'type': 'binary',
            'datas_fname': filename,
            'datas': excel_data.encode('base64'),
            'mimetype': 'application/vnd.ms-excel',
            'company_id': self.env.user.company_id.id,
        })
        return attachment.id

    @api.model
    def get_tmp_path(self, filename):
        return os.path.join(config['data_dir'], 'filestore', self.env.cr.dbname, filename)


class calendar_export_attendees(models.Model):
    _name = 'calendar.export.attendees'

    name = fields.Char('Name')
    partner_ids = fields.Many2many('res.partner', 'export_calendar_attendees_res_partner_rel', 'id1', 'id2',
                                   'Attendees')
