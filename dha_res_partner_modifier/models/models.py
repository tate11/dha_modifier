# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class dha_res_partner_mofifier(models.Model):
#     _name = 'dha_res_partner_mofifier.dha_res_partner_mofifier'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100