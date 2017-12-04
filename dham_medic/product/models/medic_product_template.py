# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends('name')
    def _compute_uper_name(self):
        for record in self:
            record.uper_name = record.name.upper()

    re_sequence = fields.Integer('Report Sequence', default=3)
    service_type = fields.Many2one('medic.test.type', 'Service Type')
    create_medical_bill = fields.Boolean('Create Medical Bill', default=False)
    buildings_type = fields.Many2one('hr.department.building.type', 'Buildings Type')
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Sex')
    uper_name = fields.Char('Uper Name', compute='_compute_uper_name')

    is_lab_test = fields.Boolean('Is Lab Test', compute='_compute_is_lab_test')
    lab_test_data = fields.One2many('medic.medical.labtest.criteria', 'product_id', 'Lab Test Results')
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'product_template_id', 'Consumable Supplies')
    married_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
    ], 'Married Status')

    @api.depends('service_type', 'type')
    def _compute_is_lab_test(self):
        try:
            test_type = self.env.ref('dham_medic.medic_test_type_lab_test')
            for record in self:
                if record.type == 'service':
                    if record.service_type and record.service_type == test_type:
                        record.is_lab_test = True
        except:
            pass

    @api.onchange('create_medical_bill', 'sex')
    def onchange_create_medical_bill(self):
        if self.create_medical_bill:
            self.service_type = False
        if not self.sex:
            self.married_status = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):

        res = super(ProductProduct, self).name_get()
        result = []

        for a in res:
            product = self.browse(a[0])
            name = a[1]
            if product and product.sex:
                sex_name = ' ( ' + product.sex
                name = name + sex_name + ((' - ' + product.married_status + ' )') if product.married_status else  ' )')
            result.append((a[0], name))
        return result
