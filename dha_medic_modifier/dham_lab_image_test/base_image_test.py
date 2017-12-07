# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

class BaseTest(models.Model):
    _name = 'base.image.test'
    _inherit = 'mail.thread'

    TYPE_ID = False

    @api.model
    def _get_default_type(self):
        try:
            return self.env.ref(self.TYPE_ID).id
        except:
            return False

    @api.model
    def _get_center_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if employee_id:
            if employee_id[0].department_id:
                return employee_id[0].department_id.find_center()
        return False

    name = fields.Char('Number', readonly=1, default='/')
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done')],
                             'Status', default='new', track_visibility='onchange', index=1)
    type = fields.Many2one('medic.test.type', string='Type', required=1, track_visibility='onchange', default=_get_default_type)

    patient = fields.Many2one('dham.patient', 'Patient', track_visibility='onchange', index=1)
    customer = fields.Many2one('res.partner', 'Customer', track_visibility='onchange', index=1)
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='customer.sex', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)

    center_id = fields.Many2one('hr.department', 'Center', default=_get_center_id, domain=[('type', '=', 'center')],
                                track_visibility='onchange')

    product_test = fields.Many2one('product.product', 'Service', required=1, track_visibility='onchange')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medic_img_id', 'Consumable Supplies')

    doctor_id = fields.Many2one('hr.employee', 'Physician')
    doctor_assign = fields.Many2one('hr.employee', 'Assigned By', track_visibility='onchange')
    assign_date = fields.Datetime('Assigned Date', default=lambda *a: datetime.datetime.now(),
                                  track_visibility='onchange')
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_img_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')
    is_adding = fields.Boolean('Check adding service', default=False)
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', copy=False)


    result_template = fields.Many2one('medic.test.res.template', 'Template')
    result = fields.Text('Description', track_visibility='onchange')  # mo ta (ket qua)
    note = fields.Text('Note', track_visibility='onchange')

    image_res1 = fields.Binary("Image 1", attachment=True)
    image_res2 = fields.Binary("Image 2", attachment=True)
    image_res3 = fields.Binary("Image 3", attachment=True)
    image_res4 = fields.Binary("Image 4", attachment=True)
    image_res5 = fields.Binary("Image 5", attachment=True)
    image_res6 = fields.Binary("Image 6", attachment=True)

    @api.onchange('result_template')
    def onchange_result_template(self):
        if self.result_template:
            result = ''
            if self.result:
                self.result += '<br/>'
            self.result = result + self.result_template.template

    @api.multi
    def action_reset_processing(self):
        data = {'state': 'processing'}
        self.write(data)

    @api.multi
    def action_processing(self):
        data = {'state': 'processing'}
        employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
        if employee:
            data['doctor_id'] = employee.id
        self.write(data)

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        self.consumable_supplies._apply_stock_(self.center_id)

    @api.onchange('product_test')
    def onchange_test_type_id(self):
        self.consumable_supplies = False
        if self.product_test:
            datas = self.consumable_supplies._get_product_qty_data(self.product_test)
            for data in datas:
                self.consumable_supplies += self.consumable_supplies.new(data)

    @api.model
    def create(self, vals):
        code = False
        # if vals.get('type', False):
        #     code = self.env['medic.test.type'].search([('id', '=', vals['type'])], limit=1).code or False
        # if code:
        #     vals['name'] = self.env['ir.sequence'].next_by_code(code)
        # else:
        #     vals['name'] = self.env['ir.sequence'].next_by_code('no.type.test.seq')

        if not 'consumable_supplies' in vals and 'product_test' in vals:
            products = self.env['product.product'].search([('id', '=', vals['product_test'])]) or False
            datas = self.env['medic.consumable.supplies']._get_product_qty_data(products)
            vals['consumable_supplies'] = [(0, False, data) for data in datas]
        return super(BaseTest, self).create(vals)