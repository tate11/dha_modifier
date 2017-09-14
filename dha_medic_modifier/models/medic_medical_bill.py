# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicMedicalBill(models.Model):
    _name = 'medic.medical.bill'

    name = fields.Char('Number', default=lambda self: self.env['ir.sequence'].next_by_code('medic.medical.bill'))
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done')], default='new',
                             string='Status')
    customer = fields.Many2one('res.partner', 'Customer')
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex_id = fields.Many2one('res.partner.sex', string='Sex', related='customer.sex_id', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)

    invoice_id = fields.Many2one('account.invoice', 'Invoice ID')

    center_id = fields.Many2one('hr.department', 'Center', readonly=1, store=True)
    building_id = fields.Many2one('hr.department', 'Building', readonly=1, store=True)
    room_id = fields.Many2one('hr.department', 'Room', readonly=1, store=True)
    doctor_assign = fields.Many2one('hr.employee', 'Physician')

    # related Medical Bills
    related_medical_bill_ids = fields.Many2many('medic.medical.bill', 'medic_medical_bill_medic_medical_bill_ids_rel',
                                                'id1', 'id2', 'Related Medical Bills')

    # don thuoc
    medicine_orders = fields.One2many('medicine.order', 'medical_id', 'Medicine Bill')

    # tab sinh hieu (Vital sign)
    # huyet ap
    blood_pressure = fields.Char('Blood Pressure (mmHg)')
    # mach
    pulse = fields.Char('Pulse (per min)')
    # nhiet do
    temperatures = fields.Char('Temperatures')
    # nhip tho
    pace_of_breathe = fields.Char('Pace of Breathe (per min)')
    height = fields.Char('Height (Cm)')
    weight = fields.Char('Weight (Kg)')
    bmi = fields.Char('BMI')
    # di ung thuoc
    allergy = fields.Many2many('product.product', 'medical_bill_product_product_rel', 'medical_id', 'product_id',
                               'Allergy')
    special = fields.Text('Special')
    note = fields.Text('Note')
    # tab Dieu tri
    # trieu chung
    prognostic = fields.Text('Prognostic')
    # chuan doan
    diagnose_icd = fields.Many2many('medic.diseases', 'medical_bill_diseases_rel', 'medical_bill_id', 'diseases_id',
                                    'Diagnose ICD')
    diagnose = fields.Text('Diagnose')
    treatment_note = fields.Text('Note')

    # tab xet nghiem
    medic_test_ids = fields.One2many('medic.test', 'medical_bill_id', 'Tests')
    medic_lab_test_compute_ids = fields.Many2many('medic.test', 'Lab Tests', compute='_get_medic_test_ids')
    medic_image_test_compute_ids = fields.Many2many('medic.test', 'Image Tests', compute='_get_medic_test_ids')

    # tab Appoint
    appoint_ids = fields.One2many('medic.appoint', 'medical_bill_id', 'Appoint')

    # services
    service_ids = fields.Many2many('product.product', 'medic_medical_bill_product_product_rel', 'medical_bill_id',
                                   'product_id', 'Services')

    def _get_medic_test_ids(self):
        MedictTest = self.env['medic.test']
        lab_type = [self.env.ref('dha_medic_modifier.medic_test_type_lab_test').id]
        image_type = [self.env.ref('dha_medic_modifier.medic_test_type_image_test').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_echograph').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram').id]
        for record in self:
            test_ids = MedictTest.search([('related_medical_bill', 'in', [record.id])])
            record.medic_lab_test_compute_ids = MedictTest.search([('id', 'in', test_ids.ids),('type','in',lab_type)])
            record.medic_image_test_compute_ids = MedictTest.search([('id', 'in', test_ids.ids),('type','in',image_type)])


class ResPartner(models.Model):
    _inherit = 'res.partner'

    medical_bill_ids = fields.One2many('medic.medical.bill', 'customer', 'Medical Bill')
