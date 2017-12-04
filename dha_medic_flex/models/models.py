# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime
import MySQLdb
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT



class MedicMedicalBill(models.Model):
    _inherit = 'medic.medical.bill'

    @api.multi
    def action_get_lab_test_res(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.lab.res.flex',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': False,
            'context': {}
        }


class MedicContract(models.Model):
    _inherit = 'res.partner.company.check'

    flex_id = fields.Char('Flex Contract Id')
    get_emp_time = fields.Datetime('Get Emp Time')

    @api.multi
    def action_get_emp_flex(self):
        self.write({'get_emp_time' : fields.Datetime.now()})
        Partner = self.env['res.partner']
        if not self.flex_id:
            raise UserError('Missing Flex Contract Id')
        conn = MySQLdb.connect(host='113.161.80.198', user='root', passwd='dha@123@', db='flexclinic', port=13306,
                               use_unicode=True, charset='utf8')
        cur = conn.cursor()
        count = cur.execute("""
            SELECT patient_id, full_name, sex, marriage_status, birthday_day, birthday_month, birthday_year, address, phone 
            FROM hpm_patient
            WHERE contract_id='%s';
        """%(self.flex_id))
        if count > 0:
            datas = cur._rows
            for data in datas:
                dob = False
                mobile = False if (data[8] == '0' or data[8] == '') else data[8]
                try:
                    dob = datetime(year=data[6], month=data[5], day=data[4]).strftime(DEFAULT_SERVER_DATE_FORMAT)
                except:
                    pass
                duplicate = self.check_partner_duplicate(data[1], mobile, dob, self.company_id)
                if duplicate:
                    duplicate.write({
                        'flex_id': data[0] or '',
                        'parent_id': self.company_id.id,  
                    })
                    Partner += duplicate
                if not duplicate:
                    tmp_data = {
                        'flex_id': data[0]  or '',
                        'name': data[1].title()  or '',
                        'sex' : 'male' if data[2] == 1 else 'female',
                        'married_status': 'single' if data[3] == 0 else 'married',
                        'description' : data[7] or '',
                        'day_of_birth' : dob,
                        'parent_id': self.company_id.id  or False,
                        'mobile': mobile,
                        'is_patient' : True,
                    }
                    Partner += Partner.with_context(from_external_center=True).create(tmp_data)
        if Partner:
            self.write({
                'employees' : [(6, 0, Partner.ids)]
            })
        cur.close()
        conn.close()

    @api.model
    def check_partner_duplicate(self, name, mobile, dob, comany_id):
        if dob == '':
            dob = False
        if mobile == '':
            mobile = False
        Partners = self.env['res.partner']
        dup_mobile = False
        dup_dob = False
        if mobile:
            dup_mobile = Partners.search([('name', '=', name), ('mobile', '=', mobile)])
        if dob:
            dup_dob = Partners.search([('name', '=', name), ('day_of_birth', '=', dob)])
        # kiểm tra xem nhân viên có đổi công ty không
        if dup_mobile:
            Partners += dup_mobile
        elif dup_dob:
            Partners += dup_dob
        if not Partners:
            return False

        match_company = Partners.filtered(lambda r: r.parent_id.id == comany_id.id)
        if not match_company:
            return Partners
        return match_company


class ResPartner(models.Model):
    _inherit = 'res.partner'

    flex_id = fields.Char('Flex ID')
