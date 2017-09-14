# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class WizardCheckCustomer(models.TransientModel):
    _name = 'wizard.check.partner'

    name = fields.Char('Customer Name')
    mobile = fields.Char('Mobile')
    cmnd = fields.Char('CMND/PassPort')

    @api.multi
    def action_check_customer(self):
        Partner = self.env['res.partner']
        for record in self:
            if record.mobile:
                Partner += Partner.search([('mobile', 'like', record.mobile)])
            if record.name:
                Partner += Partner.search([('name', '=', record.name)])
            if record.cmnd:
                Partner += Partner.search([('cmnd_passport', '=', record.cmnd)])
            if Partner:
                return {
                    'name': _('Matched Patients'),
                    'view_type': 'form',
                    'view_mode': 'tree,form,kanban',
                    'res_model': 'res.partner',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': False,
                    'domain': [('id', 'in', Partner.ids)],
                    'context': {'tree_view_ref': 'dha_medic_modifier.check_parner_wizard',
                                'form_view_ref': 'dha_medic_modifier.view_patients_form'},
                }
            else:
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'res.partner',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': False,
                    'context': {'default_name': record.name, 'default_mobile': record.mobile, 'default_is_patient' : True,
                                'default_cmnd_passport': record.cmnd, 'form_view_ref': 'dha_medic_modifier.view_patients_form'}
                }
