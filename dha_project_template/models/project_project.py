# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectTemplate(models.Model):
    _name = 'project.template'

    name = fields.Char('Name')
    line_ids = fields.One2many('project.template.line', 'parent_id')

class ProjectTemplateLine(models.Model):
    _name = 'project.template.line'

    name = fields.Char('Name')
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Assigned to')
    partner_ids = fields.Many2many('res.partner', 'project_template_line_res_partner_rel', 'line_id', 'partner_id', 'Followers')
    tag_ids = fields.Many2many('project.tags', 'project_template_line_project_tags_rel', 'line_id', 'tag_id', 'Tags')
    deadline_duration = fields.Float('Deadline (Days)')
    parent_id = fields.Many2one('project.template', 'Parent ID', required=1, readonly=1, ondelete='cascade')
