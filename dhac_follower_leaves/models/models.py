# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Holidays(models.Model):

    _inherit = "hr.holidays"

    @api.model
    def create(self, vals):
        Follower = self.env['mail.followers']

        if 'employee_id' in vals:
            emp = self.env['hr.employee'].search([('id','=',vals['employee_id'])])
            if emp and emp.parent_id and emp.parent_id.user_id:
                message_follower_ids = \
                Follower.sudo()._add_follower_command('hr.holidays', [], {emp.parent_id.user_id.partner_id.id : None}, {}, force=False)[0]
                vals['message_follower_ids'] = message_follower_ids
        return super(Holidays, self).create(vals)

    @api.multi
    def write(self, vals):
        Follower = self.env['mail.followers']

        if 'employee_id' in vals:
            emp = self.env['hr.employee'].search([('id', '=', vals['employee_id'])])
            if emp and emp.parent_id and emp.parent_id.user_id:
                message_follower_ids = \
                    Follower.sudo()._add_follower_command('hr.holidays', [],
                                                          {emp.parent_id.user_id.partner_id.id: None}, {}, force=False)[
                        0]
                vals['message_follower_ids'] = message_follower_ids
        return super(Holidays, self).write(vals)