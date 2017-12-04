# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class DocumentSubmit(models.Model):
    _name = 'dha.document.submit'
    _description = 'Document Submit Request'
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.model
    def _default_department_id(self):
        emp = self.env.user.employee_ids or False
        if emp:
            return emp[0].department_id.id or False

    @api.model
    def _default_manager_emp(self):
        try:
            return self.env.user.employee_ids[0].parent_id.user_id.id
        except:
            return False

    @api.model
    def _get_domain_request_to(self):
        res_ids = self.env.ref('dha_office_modifier.group_doc_sub_manager').users.ids
        return [('id', 'in', res_ids)]
    
    name = fields.Char('Name', required=1, track_visibility='onchange')
    type = fields.Many2one('dha.document.submit.type', 'Document Type', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submmited'),
        ('received','Received'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
    ], 'State', default='draft', track_visibility='onchange')
    request_by = fields.Many2one('res.users', 'Requested By', default=lambda self: self._uid, required=1, readonly=1,
                                 track_visibility='onchange')
    request_to = fields.Many2one('res.users', 'Requested To', default=_default_manager_emp, required=1,
                                 track_visibility='onchange', domain=_get_domain_request_to)
    department_id = fields.Many2one('hr.department', 'Department', default=_default_department_id, readonly=1)
    attachment_ids = fields.Many2many('ir.attachment', 'dha_document_submit_attachment_rel', 'document_submit_id',
                                      'attachment_id', 'Attachments')
    priority = fields.Selection([('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')],
                                'Priority', default='1', track_visibility='onchange')
    deadline = fields.Datetime('Deadline', track_visibility='onchange')
    date = fields.Datetime('Creation Date', default=lambda self: fields.Datetime.now(), track_visibility='onchange',
                           readonly=1)
    return_date = fields.Datetime('Returned Time', track_visibility='onchange')
    note = fields.Text('Note')

    @api.multi
    def action_submit(self):
        self.write({'state': 'submitted'})

    @api.multi
    def action_signed(self):
        self.write({'state': 'signed'})

    @api.multi
    def action_rejected(self):
        self.write({'state': 'rejected'})

    @api.multi
    def action_reset(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_return(self):
        self.write({'return_date': fields.Datetime.now()})

    @api.multi
    def action_receive(self):
        records = self.filtered(lambda r: r.state == 'submitted')
        for record in records:
            if record.request_to:
                record.message_subscribe_users(user_ids=[record.request_to.id], subtype_ids=[
                    self.env.ref('dha_office_modifier.mt_doc_submit_request_received').id])
        records.write({'state': 'received'})

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state in ['submitted', 'signed', 'rejected']:
            return 'dha_office_modifier.mt_doc_submit_request'
        elif 'state' in init_values and self.state in ['received']:
            return 'dha_office_modifier.mt_doc_submit_request_received'
        return super(DocumentSubmit, self)._track_subtype(init_values)


class DocumentSubmitType(models.Model):
    _name = 'dha.document.submit.type'

    name = fields.Char('Name', required=1)
