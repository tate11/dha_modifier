# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class email_reminder(models.Model):
    _name = 'email.reminder'

    @api.model
    def _default_task_type(self):
        return self.env['project.task.type'].search([('name', 'not in', ['Done', 'Solved', 'HOAN THANH'])])

    @api.model
    def _default_helpdesk_type(self):
         return self.env['helpdesk.stage'].search([('name', 'not in', ['Done', 'Solved'])])

    name = fields.Char('Name', default='Email Reminder')
    project_task_type_ids = fields.Many2many('project.task.type', string='Project Task Type', default=_default_task_type)
    helpdesk_stage_ids = fields.Many2many('helpdesk.stage', string='Helpdesk Stage', default=_default_helpdesk_type)

    @api.model
    def send_email_reminder(self):
        PR = self.env['purchase.request']
        PO = self.env['purchase.order']
        LR = self.env['hr.holidays']
        PT = self.env['project.task']
        HT = self.env['helpdesk.ticket']

        template = self.env.ref('dha_medic_reminder.reminder_email_template')
        current_host = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        config = self.search([], limit=1, order='id desc')
        if config:
            project_task_type_ids = config.project_task_type_ids.ids
            helpdesk_stage_ids = config.helpdesk_stage_ids.ids
        else:
            project_task_type_ids = self.env['project.task.type'].search([('name', 'not in', ['Done', 'Solved', 'HOAN THANH'])]).ids
            helpdesk_stage_ids = self.env['helpdesk.stage'].search([('name', 'not in', ['Done', 'Solved','Cancelled'])]).ids

        for user in self.env['res.users'].search([]):
            count = {'project_task_ids': 0, 'purchase_request_ids': 0, 'purchase_order_ids': 0, 'hr_holiday_ids': 0, 'helpdesk_ticket_ids': 0}
            if user.has_group('dha_medic_reminder.group_mail_reminder'):
                # get pending task
                try:
                    project_task_ids = PT.with_env(self.env(user=user.id)).search([
                    ('stage_id', 'in', project_task_type_ids), ('user_id', '=', user.id),
                    ('active', '=', True)])
                    count['project_task_ids'] = len(project_task_ids)
                except Exception:
                    project_task_ids = None

                # get pending purchase request
                try:
                    purchase_request_ids = PR.with_env(self.env(user=user.id)).search(['|',
                       '&', ('state', '=', 'draft'), ('assigned_to', '=', user.id),
                       '&', ('state', '=', 'to_approve'), ('master_approver', '=', user.id)])
                    count['purchase_request_ids'] = len(purchase_request_ids)
                except Exception:
                    purchase_request_ids = None

                # get pending purchase order
                try:
                    purchase_order_ids = None
                    if user.has_group('dhac_double_approve_pr.group_purchase_leader'):
                        purchase_order_ids = PO.with_env(self.env(user=user.id)).search([
                            ('state', 'in', ('to approve', 'accepted'))])
                        count['purchase_order_ids'] = len(purchase_order_ids)
                except Exception:
                    purchase_order_ids = None

                # get pending leaving request
                try:
                    hr_holiday_ids = LR.with_env(self.env(user=user.id)).search([
                        ('state', 'in', ('validate1', 'confirm')), ('user_manager_id', '=', user.id)])
                    count['hr_holiday_ids'] = len(hr_holiday_ids)
                except Exception:
                    hr_holiday_ids = None

                # get pending ticket
                try:
                    helpdesk_ticket_ids = HT.with_env(self.env(user=user.id)).search([
                    ('user_id', '=', user.id), ('stage_id', 'in', helpdesk_stage_ids)])
                    count['helpdesk_ticket_ids'] = len(helpdesk_ticket_ids)
                except Exception:
                    helpdesk_ticket_ids = None

                data = {
                    'partner_id': user.partner_id,
                    'current_host': current_host,
                    'count': count,
                    'project_task_ids': project_task_ids,
                    'purchase_request_ids': purchase_request_ids,
                    'hr_holiday_ids': hr_holiday_ids,
                    'helpdesk_ticket_ids': helpdesk_ticket_ids,
                    'purchase_order_ids': purchase_order_ids
                }

                if count.get('project_task_ids', False) or count.get('purchase_request_ids', False) or count.get('purchase_order_ids', False) or count.get('hr_holiday_ids', False) or count.get('helpdesk_ticket_ids', False):
                    template.with_context(data).send_mail(user.id,force_send=True)