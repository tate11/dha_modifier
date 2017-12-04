from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, config


class WizardProjectTemplate(models.Model):
    _name = 'wizard.project.template'

    name = fields.Char('Name')
    assign_time = fields.Datetime('Assign Time', required=1)
    template_ids = fields.Many2many('project.template', 'wizard_project_template_project_template_rel', 'wizard_id',
                                    'template_id', string='Template', required=1)

    @api.multi
    def do_action(self):
        Task = self.env['project.task']
        Follower = self.env['mail.followers']
        active_model = self.env.context.get('active_by_project', False)
        if not active_model:
            try:
                active_model = self.env[self.env.context.get('active_model', False)].browse(
                    self.env.context.get('active_id', False))
            except:
                return
        for tmp in self.template_ids:
            for line in tmp.line_ids:
                deadline = (datetime.strptime(self.assign_time, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(
                    days=line.deadline_duration)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT) if line.deadline_duration else False

                partners = {}
                for partner in line.partner_ids:
                    partners[partner.id] = None

                message_follower_ids = Follower.sudo()._add_follower_command('project.task', [], partners, {}, force=False)[0]
                new_task = Task.with_context(mail_create_nosubscribe = True).create({
                    'name': line.name,
                    'project_id': active_model.id,
                    'user_id': line.user_id.id or False,
                    'tag_ids': [(6, 0, line.tag_ids.ids)],
                    'date_assign': self.assign_time,
                    'date_deadline': deadline,
                    'description' :  line.description or '',
                    'message_follower_ids' : message_follower_ids,
                })

