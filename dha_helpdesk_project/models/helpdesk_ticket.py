# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def message_new(self, msg, custom_values=None):
        if custom_values is None:
            custom_values = {}
        FetchMail = self.env['fetchmail.server'].sudo()
        if self._context.get('fetchmail_server_id', False):
            server_id = FetchMail.search([('id', '=', self._context.get('fetchmail_server_id'))])
            if server_id:
                team_id = server_id.helpdesk_team
                if team_id:
                    custom_values['team_id'] = team_id.id
        return super(HelpdeskTicket, self).message_new(msg, custom_values=custom_values)

    @api.multi
    def write(self, vals):
        Stage = self.env['helpdesk.stage'].sudo()
        Project = self.env['project.task']
        ProjectStage = self.env['project.task.type']
        project = False
        stage_name = False
        if vals.get('stage_id', False):
            stage_id = Stage.browse(vals.get('stage_id'))
            if stage_id:
                if stage_id.project_id:
                    project = stage_id.project_id
                    stage_name = stage_id.name
        if project:
            project_stage = False
            if stage_name:
                project_stage = ProjectStage.search([('name','=',stage_name),('project_ids','in', [project.id])], limit=1)

            for record in self:
                message_id = record.message_ids.filtered(lambda r: r.message_type == 'email')
                new_message = message_id[-1].copy()
                task_vals = {
                    'project_id' : project.id or False,
                    'user_id' : record.user_id.id or False,
                    'name': record.display_name,
                    'stage_id' : project_stage.id if project_stage else False,
                    'description' : message_id[-1].body if message_id else '',
                    'helpdesk_id' : record.id,
                }
                new_project = Project.create(task_vals)
                new_message.write({'model': 'project.task', 'res_id' : new_project.id})
        return super(HelpdeskTicket, self).write(vals)

    @api.multi
    def assign_ticket_to_self(self):
        res =  super(HelpdeskTicket, self).assign_ticket_to_self()
        Stage = self.env['helpdesk.stage']
        for record in self:
            if record.team_id:
                stage_id = Stage.search([('name','=','Processing'),('team_ids','in',[record.team_id.id])])
                if stage_id:
                    record.write({'stage_id' : stage_id.id})
        return res

class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    project_id = fields.Many2one('project.project', 'Project')