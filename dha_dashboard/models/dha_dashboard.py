# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    dash_info = fields.Char('Dashboard Info', compute='_compute_dash_info', store=True)

    @api.depends('requested_by')
    def _compute_dash_info(self):
        for rec in self:
            if rec.requested_by:
                rec.dash_info = '%s - %s' % (rec.requested_by.name, datetime.strptime(rec.create_date,
                                                                                      DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))
            else:
                rec.dash_info = '%s' % (datetime.strptime(rec.create_date,
                                                          DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    dash_info = fields.Char('Dashboard Info', compute='_compute_dash_info', store=True)

    @api.depends('respond_id')
    def _compute_dash_info(self):
        for rec in self:
            if rec.respond_id:
                rec.dash_info = '%s - %s' % (rec.respond_id.name, datetime.strptime(rec.create_date,
                                                                                      DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))
            else:
                rec.dash_info = '%s' % (datetime.strptime(rec.create_date,
                                                          DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))

class HrHoliday(models.Model):
    _inherit = 'hr.holidays'

    dash_info = fields.Char('Dashboard Info', compute='_compute_dash_info', store=True)
    user_manager_id = fields.Many2one('res.users', 'User Manager Id')

    @api.depends('employee_id')
    def _compute_dash_info(self):
        for rec in self:
            if rec.employee_id:
                rec.dash_info = '%s - %s' % (rec.employee_id.name, datetime.strptime(rec.create_date,
                                                                                      DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))
            else:
                rec.dash_info = '%s' % (datetime.strptime(rec.create_date,
                                                          DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    '%d/%m/%Y'))

    @api.model
    def create(self, vals):
        if vals.get('employee_id', False):
            try:
                vals['user_manager_id'] = self.env['hr.employee'].search([('id','=',vals['employee_id'])]).parent_id.user_id.id
            except:
                pass
        return super(HrHoliday, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('employee_id', False):
            try:
                vals['user_manager_id'] = self.env['hr.employee'].search(
                    [('id', '=', vals['employee_id'])]).parent_id.user_id.id
            except:
                pass
        return super(HrHoliday, self).write(vals)

    @api.model
    def compute_old_data_manager(self):
        for record in self.search([]):
            if record.employee_id:
                if record.employee_id.parent_id and record.employee_id.parent_id.user_id:
                    record.write({'user_manager_id': record.employee_id.parent_id.user_id.id})