# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'
    _order = 'id desc'

    @api.model
    def _get_default_assignee(self):
        emp = self.env.user.employee_ids or False
        if emp:
            return emp[0].department_id.manager_id.user_id.id or False
        return False

    @api.model
    def _get_domain_master_approver(self):
        pr_manager = self.env.ref('purchase_request.group_purchase_request_manager')
        return [('id', 'in', pr_manager.users.ids)]

    @api.depends('assigned_to')
    def _compute_check_approver(self):
        for record in self:
            if self._uid == record.assigned_to.id:
                record.check_approve1 = True

    @api.model
    def _get_default_master_approver(self):
        emp = self.env.user.employee_ids or False
        if emp:
            return emp[0].department_id.manager_id.parent_id.user_id.id or False
        return False

    @api.model
    def _default_department_id(self):
        emp = self.env.user.employee_ids or False
        if emp:
            return emp[0].department_id.id or False

    assigned_to = fields.Many2one('res.users', 'Approver Lv1', track_visibility='onchange',
                                  default=_get_default_assignee, required=1)
    master_approver = fields.Many2one('res.users', 'Approver Lv2', track_visibility='onchange', required=1,
                                      domain=_get_domain_master_approver, default=_get_default_master_approver)
    department_id = fields.Many2one('hr.department', string='Department', default=_default_department_id, readonly=1)
    dead_line = fields.Datetime('Deadline')
    check_approve1 = fields.Boolean('Check Approver 1', compute='_compute_check_approver')
    date_start = fields.Datetime('Creation date', help="Date when the user initiated the request.",
                                 default=lambda self: datetime.now(), track_visibility='onchange', readonly=1)
    submit = fields.Boolean('Submit', default=False, track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'submit': True})

    @api.multi
    def write(self, vals):
        if vals.get('state'):
            if vals['state'] == 'to_approve':
                for request in self:
                    if request.master_approver:
                        request.message_subscribe_users(user_ids=[request.master_approver.id], subtype_ids=[
                            self.env.ref('purchase_request.mt_request_to_approve').id])
        res = super(PurchaseRequest, self).write(vals)
        if vals.get('assigned_to'):
            for request in self:
                request._fix_follower_approver_lv1()
        return res

    @api.model
    def create(self, vals):
        request = super(PurchaseRequest, self).create(vals)
        if vals.get('assigned_to'):
            request._fix_follower_approver_lv1()
        return request

    @api.model
    def _fix_follower_approver_lv1(self, ):
        follow = self.env['mail.followers'].sudo().search(
            [('res_model', '=', 'purchase.request'), ('res_id', '=', self.id),
             ('partner_id', '=', self.assigned_to.partner_id.id)])
        submit = self.env.ref('dhac_double_approve_pr.mt_request_submit').id
        follow.write({'subtype_ids': [(4, submit)]})

    # @api.multi
    # def button_approved(self):
    #     if self.env.user.user_has_groups('purchase_request.group_purchase_request_manager'):
    #         return super(PurchaseRequest, self).button_approved()
    #     raise UserError ('You have no access to do this.')

    @api.multi
    def _track_subtype(self, init_values):
        for rec in self:
            if 'state' in init_values and rec.state == 'to_approve':
                return 'purchase_request.mt_request_to_approve'
            elif 'state' in init_values and rec.state == 'approved':
                return 'purchase_request.mt_request_approved'
            elif 'state' in init_values and rec.state == 'rejected':
                return 'purchase_request.mt_request_rejected'
            if 'assigned_to' in init_values:
                return 'dhac_double_approve_pr.mt_request_assign'
            if 'submit' in init_values and rec.submit == True:
                return 'dhac_double_approve_pr.mt_request_submit'
        return super(PurchaseRequest, self)._track_subtype(init_values)


class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    product_categ_id = fields.Many2one('product.category', 'Product Category', related='product_id.categ_id',
                                       readonly=1, store=True)
    purchase_respond_id = fields.Many2one('res.users', 'Purchase Respond',
                                          related='product_id.categ_id.purchase_respond_id', readonly=1, store=True)
    date_start = fields.Datetime(related='request_id.date_start', string='Request Date', readonly=True, store=True)
    name = fields.Text('Description', size=256, track_visibility='onchange')
