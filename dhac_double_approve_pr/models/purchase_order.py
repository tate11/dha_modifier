# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.model
    def _get_domain_respond_id(self):
        res_ids = self.env.ref('purchase.group_purchase_user').users.ids
        return [('id','in', res_ids)]

    respond_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user.id, domain=_get_domain_respond_id, readonly=1)
    referent_po_ids = fields.Many2many('purchase.order', 'purchase_order_references_purchase_order_rel', 'id1', 'id2', 'Reference Purchase Orders')
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('accepted','Vendor Accepted'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    @api.multi
    def button_accept(self):
        return self.write({'state': 'accepted'})

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['accepted']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                                and order.amount_total < self.env.user.company_id.currency_id.compute(
                            order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'purchase':
            return 'purchase.mt_rfq_approved'
        if 'state' in init_values and self.state == 'accepted':
            return 'dhac_double_approve_pr.mt_rfq_accepted'
        elif 'state' in init_values and self.state == 'to approve':
            return 'purchase.mt_rfq_confirmed'
        elif 'state' in init_values and self.state == 'done':
            return 'purchase.mt_rfq_done'
        return super(PurchaseOrder, self)._track_subtype(init_values)

    @api.multi
    def write(self, vals):

        if vals.get('state', False):
            lead_group = self.env.ref('dhac_double_approve_pr.group_purchase_leader')
            manager_group = self.env.ref('purchase.group_purchase_manager')
            lead_user = lead_group.users - manager_group.users
            for purchase in self:
                if vals.get('state', False) == 'accepted':
                    if lead_user:
                        purchase.message_subscribe_users(user_ids=lead_user.ids, subtype_ids=[
                            self.env.ref('dhac_double_approve_pr.mt_rfq_accepted').id, self.env.ref('purchase.mt_rfq_approved').id])
                        
                elif vals.get('state', False) == 'to approve':
                    if manager_group.users:
                        purchase.message_subscribe_users(user_ids=manager_group.users.ids, subtype_ids=[
                            self.env.ref('purchase.mt_rfq_confirmed').id])
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('respond_id', False):
            self.message_subscribe_users(user_ids=[vals.get('respond_id')])
        return res