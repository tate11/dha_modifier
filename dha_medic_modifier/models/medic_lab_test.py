# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicLabTest(models.Model):
    _name = 'medic.test'
    _description = 'Medic Test'
    _inherit = 'mail.thread'
    _order = 'type, id desc'


    @api.model
    def _get_center_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if employee_id:
            if employee_id[0].department_id:
                return employee_id[0].department_id.find_center()
        return False

    @api.depends('type')
    def _compute_show_image(self):
        for record in self:
            try:
                record.show_image = (record.type != self.env.ref('dha_medic_modifier.medic_test_type_lab_test'))
            except:
                continue

    name = fields.Char('Number', readonly=1, default='/')
    state = fields.Selection([('new', 'New'), ('ready', 'Ready'), ('processing', 'Processing'), ('done', 'Done')], 'Status', default='new', track_visibility='onchange')
    type = fields.Many2one('medic.test.type', string='Type', required=1, track_visibility='onchange')
    show_image = fields.Boolean('Show Image', compute='_compute_show_image')

    patient = fields.Many2one('dham.patient', 'Patient', track_visibility='onchange', index=1)
    customer = fields.Many2one('res.partner', 'Customer', track_visibility='onchange')
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='customer.sex', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)
    center_id = fields.Many2one('hr.department', 'Center', default=_get_center_id, domain=[('type', '=', 'center')], track_visibility='onchange')

    product_test = fields.Many2one('product.product', 'Service', required=1, track_visibility='onchange')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medic_test_id', 'Consumable Supplies')
    
    doctor_id = fields.Many2one('hr.employee', 'Physician')
    doctor_assign = fields.Many2one('hr.employee', 'Assigned By', track_visibility='onchange')
    assign_date = fields.Datetime('Assigned Date', default=lambda *a: datetime.datetime.now(), track_visibility='onchange')
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')
    is_adding = fields.Boolean('Check adding service', default=False)
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', copy=False)

    lab_test_criteria = fields.One2many('medic.medical.lab.resultcriteria', 'medical_lab_test_id', string='Lab Test Result')
    
    result_template = fields.Many2one('medic.test.res.template', 'Template')
    result = fields.Text('Description', track_visibility='onchange' ) # mo ta (ket qua)
    note = fields.Text('Note', track_visibility='onchange')

    image_res1 = fields.Binary("Image 1", attachment=True, track_visibility='onchange')
    image_res2 = fields.Binary("Image 2", attachment=True, track_visibility='onchange')
    image_res3 = fields.Binary("Image 3", attachment=True, track_visibility='onchange')
    image_res4 = fields.Binary("Image 4", attachment=True, track_visibility='onchange')
    image_res5 = fields.Binary("Image 5", attachment=True, track_visibility='onchange')
    image_res6 = fields.Binary("Image 6", attachment=True, track_visibility='onchange')
    
    @api.onchange('result_template')
    def onchange_result_template(self):
        if self.result_template:
            result = ''
            if self.result:
                self.result += '<br/>'
            self.result = result + self.result_template.template


    @api.multi
    def action_ready(self):
        data = {'state': 'ready'}
        self.write(data)

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

    @api.model
    def create(self, vals):
        code = False
        if vals.get('type', False):
            code = self.env['medic.test.type'].search([('id', '=', vals['type'])], limit=1).code or False
        if code:
            vals['name'] = self.env['ir.sequence'].next_by_code(code)
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('no.type.test.seq')
        if not 'lab_test_criteria' in vals and 'product_test' in vals :
            produt_tmp_id = self.env['product.product'].search([('id','=',vals['product_test'])]).product_tmpl_id.id or False
            datas = self._get_lab_criteria(produt_tmp_id)
            vals['lab_test_criteria'] = [(0, False, data) for data in datas]

        if not 'consumable_supplies' in vals and 'product_test' in vals :
            products = self.env['product.product'].search([('id','=',vals['product_test'])]) or False
            datas = self.env['medic.consumable.supplies']._get_product_qty_data(products)
            vals['consumable_supplies'] = [(0, False, data) for data in datas]
        return super(MedicLabTest, self).create(vals)

    @api.onchange('product_test')
    def onchange_test_type_id(self, test_type=False):
        self.lab_test_criteria = False
        if self.product_test:
            datas = self._get_lab_criteria(self.product_test.product_tmpl_id.id)
            for data in datas:
                self.lab_test_criteria += self.lab_test_criteria.new(data)
        self.consumable_supplies = False
        if self.product_test:
            datas = self.consumable_supplies._get_product_qty_data(self.product_test)
            for data in datas:
                self.consumable_supplies += self.consumable_supplies.new(data)

    @api.model
    def _get_lab_criteria(self, product_template_id):
        res = []
        query = _(
            "select name, sequence, normal_range, units from medic_medical_labtest_criteria where product_id=%s") % (
                    str(product_template_id))
        self.env.cr.execute(query)
        vals = self.env.cr.fetchall()
        if vals:
            for va in vals:
                specs = {
                    'name': va[0],
                    'sequence': va[1],
                    'normal_range': va[2],
                    'units': va[3],
                }
                res += [specs]
        return res


class MedicLabTestType(models.Model):
    _name = 'medic.test.type'

    name = fields.Char('Name', required=1, translate=1)
    code = fields.Char('Code')
    model_name = fields.Char('Model Name', required=1)
    
class MedicLabTestResultTemplate(models.Model):
    _name = 'medic.test.res.template'

    name = fields.Char('Name', required=1)
    type = fields.Many2one('medic.test.type', string='Type', required=1)
    template = fields.Text('Template')

class MedicLabTestResult(models.Model):
    _name = 'medic.test.result'
    _description = 'Medic Test Result'
    
    name = fields.Char('Name')


class MedicLabTestUnits(models.Model):
    _name = 'medic.medical.lab.units'
    _description = 'Lab Test Units'

    name = fields.Char(string='Unit Name', size=25, required=True)
    code = fields.Char(string='Code', size=25, required=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'The Lab unit name must be unique')]

class MedicLabTestCriteria(models.Model):
    _name = 'medic.medical.labtest.criteria'
    _description = 'Lab Test Criteria'

    name = fields.Char(string='Tests', size=128, required=True)
    normal_range = fields.Text(string='Normal Range')
    units = fields.Many2one('medic.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    product_id = fields.Many2one('product.template', string='Product Id', required=True, ondelete='cascade')

    _order="sequence"
    

class MedicLabTestsResultCriteria(models.Model):
    _name = 'medic.medical.lab.resultcriteria'
    _description = 'Lab Test Result Criteria'
    _order="sequence"
        
    name = fields.Char(string='Tests', size=128, required=True)
    result = fields.Text(string='Result')
    normal_range = fields.Text(string='Normal Range')
    units = fields.Many2one('medic.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_lab_test_id = fields.Many2one('medic.test', string='Lab Tests', required=True, ondelete='cascade')
