# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

class MedicContract(models.Model):
    _inherit = 'res.partner.company.check'

    @api.model
    def get_contract_info(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self._context['id'])])
        contract_ids = self.search([('doctor_ids','in',[employee_id.id]),('state','=','processing')])
        if len(contract_ids) >0:
            return {
                'contracts': contract_ids.read(['name','id','company_id','state']),
                'doctor_id': employee_id.id,
                'buildings_type': employee_id.department_id.buildings_type.id,
                'success': True,
            }
        return {'success': False}