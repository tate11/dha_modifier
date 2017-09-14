# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    helpdesk_team = fields.Many2one('helpdesk.team', 'Heldpesk Team')
    object_model = fields.Char(related='object_id.model', string='Model')