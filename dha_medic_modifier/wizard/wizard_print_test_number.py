# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import os

class WizardPrintTestNumber(models.TransientModel):
    _name = 'wizard.print.test.number'

    name = fields.Char('Name')
    digit_number = fields.Integer('Ditgit', default=4, required=1)

    @api.multi
    def action_print(self):
        ActiveModel = self.env['medic.test']
        digit = self.digit_number
        for record in ActiveModel.search([('id','in',self.env.context['active_ids'])]):
            number = record.name[-digit:]
        return