# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.http import request


class WizardCheckCustomer(models.TransientModel):
    _name = 'wizard.check.partner'
    _inherit = 'barcodes.barcode_events_mixin'

    name = fields.Char('Customer Name')
    mobile = fields.Char('Mobile')
    day_of_birth = fields.Date('Date of Birth')
    cmnd = fields.Char('CMND/PassPort')

    def on_barcode_scanned(self, barcode):
        Partner = self.env['res.partner'].sudo()
        if barcode:
            partner_id = Partner.search([('customer_id', '=', barcode)])
            if partner_id:
                menu_id = self.env.ref('dha_medic_modifier.action_partner_patients_form').id
                action = self.env.ref('dha_medic_modifier.menu_medic_root').id
                request.redirect('web#id=%s&view_type=form&model=res.partner&menu_id=%s&action=%s' % (
                    partner_id.id, menu_id.id, action.id))
            else:
                return {
                    'warning': {
                        'title': _('Warning!'),
                        'message': _('No Matched Customer!'),
                    }
                }

    @api.multi
    def action_check_customer(self):
        Partner = self.env['res.partner']
        for record in self:
            if record.mobile:
                Partner += Partner.search([('mobile', 'like', record.mobile)])
            if record.name:
                Partner += Partner.search([('name', 'like', record.name)])
            if record.day_of_birth:
                Partner += Partner.search([('name', 'like', record.name),('day_of_birth','=', record.day_of_birth)])
            # if record.cmnd:
            #     Partner += Partner.search([('cmnd_passport', '=', record.cmnd)])
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
                    'context': {'default_name': record.name, 'default_mobile': record.mobile,
                                'default_is_patient': True,
                                'default_day_of_birth': record.day_of_birth,
                                'default_cmnd_passport': record.cmnd,
                                'form_view_ref': 'dha_medic_modifier.view_patients_form'}
                }
