# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from ..service.service_read_xlsx import  ServiceReadXlsx
import base64, os, werkzeug
from odoo.modules import get_module_path
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class ImportEmployee(models.TransientModel):
    _name = 'wizard.import.employee'

    @api.multi
    def download_template_file(self):
        id = self.env['ir.attachment'].sudo().search([('datas_fname','=','import_file_template.xlsx')], limit=1).id or False
        if id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return {
                'type': 'ir.actions.act_url',
                'name': "Download File Template",
                'target': 'new',
                'url': base_url + "/web/content/%s?download=1"%(id),
            }

    name = fields.Char('Name')
    wizard_type = fields.Selection([
        ('import', 'Import'),
        ('add', 'Add')
    ], default='import', string='Type')
    file = fields.Binary('Excel File', attachment=True)
    company_id = fields.Many2one('res.partner', 'Company')

    @api.multi
    def do_action(self):
        if not self.file:
            raise UserError(_("Please upload your import file!"))
        if self.wizard_type == 'import':
            self.action_import()
        if self.wizard_type == 'add':
            self.action_add()

    @api.multi
    def action_add(self):
        ActiveObj = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        Patients = self.action_import()
        if Patients:
            ActiveObj.with_context(action_add_employee= Patients).action_validate()
        return

    @api.multi
    def action_import(self):
        Patients = self.env['dham.patient']
        ActiveObj = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        Service = ServiceReadXlsx()
        data_obj = Service.read_xls(base64.b64decode(self.file))
        header = data_obj.next()
        parsed_header = self.parse_header(header)

        index = 2
        comany_id = self.company_id
        sex_index = parsed_header.index('sex')
        day_of_birth_index = parsed_header.index('day_of_birth')
        try:
            for data in data_obj:
                tmp_data = {'parent_id': comany_id.id, 'company_id': comany_id.company_id.id}
                for i in range(len(data)):
                    if data[i] == '':
                        data[i] = False
                    tmp_data[parsed_header[i]] = data[i]
                tmp_data['day_of_birth'] = self.parse_day_of_birth(tmp_data['day_of_birth'])
                tmp_data['name'] = tmp_data['name'].title()
                check = self.check_partner_duplicate(tmp_data['name'], tmp_data['mobile'], tmp_data['day_of_birth'],comany_id)
                if check:
                    Patients += check
                else:
                    Patients += Patients.with_context(from_external_center=True).create(tmp_data)
                index += 1
        except:
            raise UserError(_("Error at line %s!"%(index)))
        Patients = Patients.search([('id','in', Patients.ids),('id','not in', ActiveObj.employees.ids)])
        if Patients:
            ActiveObj.write({'employees': [(4, x.id) for x in Patients], 'import_seq': (ActiveObj.import_seq + 1)})

        attachment = {
            'name': ActiveObj.name + ' - ' + str(ActiveObj.import_seq),
            'datas': self.file,
            'datas_fname' : ActiveObj.name + ' - ' + str(ActiveObj.import_seq) + '.xlsx',
            'res_model': ActiveObj._name,
            'res_id': ActiveObj.id,
            'company_id' : comany_id.company_id.id,
        }
        self.env['ir.attachment'].create(attachment)
        return Patients

    @api.model
    def parse_day_of_birth(self, dob):
        if dob == '':
            return False
        try:
            return datetime.strptime(dob, '%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
        except:
            try:
                return datetime.strptime(dob, '%m/%d/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
            except:
                pass
        return dob

    @api.model
    def check_partner_duplicate(self, name, mobile, dob, comany_id):
        if dob == '':
            dob = False
        if mobile == '':
            mobile = False
        Patients = self.env['dham.patient']
        dup_mobile = False
        dup_dob = False
        if mobile:
            dup_mobile = Patients.search([('name', '=', name), ('mobile', '=', mobile)])
        if dob:
            dup_dob = Patients.search([('name', '=', name), ('day_of_birth', '=', dob)])
        # kiểm tra xem nhân viên có đổi công ty không
        if dup_mobile:
            Patients += dup_mobile
        elif dup_dob:
            Patients += dup_dob
        if not Patients:
            return False

        match_company = Patients.filtered(lambda r: r.parent_id.id == comany_id.id)
        if not match_company:
            Patients.write({'parent_id': comany_id.id})
            return Patients
        return match_company

    def parse_header(self, header):
        res = []
        for head in header:
            if head == 'Name':
                res.append('name')
            elif head == 'Sex':
                res.append('sex')
            elif head == 'Day of Birth':
                res.append('day_of_birth')
            elif head == 'Mobile':
                res.append('mobile')
            elif head == 'Email':
                res.append('email')
            elif head == 'Description':
                res.append('description')
            elif head == 'Married Status':
                res.append('married_status')
        return res

    @api.model
    def create_template_attachment(self):
        Attachment = self.env['ir.attachment'].sudo()
        module_path = get_module_path('dha_medic_modifier')
        file_path = module_path + '/static/file/template_data_import.xlsx'
        file = open(file_path, 'r')
        datas = base64.b64encode(file.read())
        attachment = {
            'name': (_('Import Employees File Template')),
            'datas': datas,
            'datas_fname': (_('import_file_template.xlsx')),
            'company_id': self.env.user.company_id.id,
        }
        existed = Attachment.search([('datas_fname','=','import_file_template.xlsx')])
        if existed:
            existed.unlink()
        attachment_id = Attachment.create(attachment)
        file.close()
        return True