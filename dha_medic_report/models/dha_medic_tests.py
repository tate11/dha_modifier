# -*- coding: utf-8 -*-

from odoo import models, fields, api

class dha_medic_tests(models.Model):
    _inherit = 'medic.test'

    @api.multi
    def print_lab_test(self):
        return self.env['report'].get_action(self, 'dha_medic_report.report_lab_test')