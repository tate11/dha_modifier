# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class PartnerCompanyCheckDashBoard(models.Model):
    _inherit = 'res.partner.company.check'
    
    @api.multi
    def open_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'res.partner.company.check',
            'domain': [],
            'res_id' : self[0].id,
        }

    @api.multi
    def action_add_services(self):
        center = self.env.ref('dham_medic.out_center_department')
        for record in self:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': False,
                'context': {'form_view_ref': 'account.invoice_form', 'default_center_id': center.id,
                            'default_order_type': 'medical', 'default_contract_adding_services': record.id, 'default_pricelist_id': record.pricelist_id.id or False}
            }