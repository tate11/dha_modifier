# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicLabTest(models.Model):
    _name = 'medic.test'
    _description = 'Medic Test'
    _inherit = 'mail.thread'

    @api.model
    def _get_center_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if employee_id:
            if employee_id[0].department_id:
                return employee_id[0].department_id.find_center()
        return False

    name = fields.Char('Number', readonly=1, default='/')
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done')], 'Status', default='new')
    type = fields.Many2one('medic.test.type', string='Type', required=1)
    customer = fields.Many2one('res.partner', 'Customer')
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex_id = fields.Many2one('res.partner.sex', string='Sex', related='customer.sex_id', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)
    center_id = fields.Many2one('hr.department', 'Center', default=_get_center_id, domain=[('type', '=', 'center')])

    product_test = fields.Many2one('product.product', 'Service')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.test.consumable', 'medic_test_id', 'Consumable Supplies')

    doctor_assign = fields.Many2one('hr.employee', 'Doctor Assigned')
    assign_date = fields.Datetime('Assigned Date', default=lambda *a: datetime.datetime.now())
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')

    note = fields.Text('Note')

    @api.model
    def create(self, vals):
        code = False
        if vals.get('type', False):
            code = self.env['medic.test.type'].search([('id', '=', vals['type'])], limit=1).code or False
        if code:
            vals['name'] = self.env['ir.sequence'].next_by_code(code)
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('no.type.test.seq')
        return super(MedicLabTest, self).create(vals)


class MedicLabTestType(models.Model):
    _name = 'medic.test.type'

    name = fields.Char('Name', required=1)
    code = fields.Char('Code')


class ConsumableSupplies(models.Model):
    _name = 'medic.test.consumable'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product ID')
    qty = fields.Float('Quantity', default=1.0)
    product_uom_id = fields.Many2one('product.uom', string='Product Unit of Measure')
    medic_test_id = fields.Many2one('medic.test', string='Medict Test', required=True, ondelete='cascade')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
