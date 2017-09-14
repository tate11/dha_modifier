# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_type = fields.Many2one('medic.test.type', 'Service Type')
    create_medical_bill = fields.Boolean('Create Medical Bill', default=False)
    buildings_type = fields.Many2one('hr.department.building.type', 'Buildings Type')
    sex_id = fields.Many2one('res.partner.sex', 'Only For')

