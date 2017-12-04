# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    img_sign = fields.Binary('Employee Signature', attachment=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self.env.context.get('sub_treatment_type', False) == 'company' and self.env.context.get('sub_treatment_company_check', False):
            contract = self.env['res.partner.company.check'].sudo().search([('id','=',self.env.context.get('sub_treatment_company_check'))])
            if contract and contract.doctor_ids:
                if args is None:
                    args = []
                args.extend([('id','in', contract.doctor_ids.ids)])
        return super(HREmployee, self).name_search(name, args=args, operator=operator, limit=limit)