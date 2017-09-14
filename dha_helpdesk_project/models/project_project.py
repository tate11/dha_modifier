# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    helpdesk_id = fields.Many2one('helpdesk.ticket', 'Helpdesk ID')