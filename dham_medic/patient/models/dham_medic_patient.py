# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import base64
from odoo.modules import get_module_path
from ...service.service_read_xlsx import ServiceReadXlsx

class PatientInsurranceLines(models.Model):
    _name = 'dham.patient.insurrance.type'

    name = fields.Char('Name')

class PartnerInsurrance(models.Model):
    _name = 'dham.patient.insurrance'

    name = fields.Char('Number')
    type = fields.Many2one('dham.patient.insurrance.type')
    join_date = fields.Date('Create Date')
    expiry_date = fields.Date('Expiry Date')
    patient_id = fields.Many2one('dham.patient', 'Patient ID', required=True, ondelete='cascade')
    # ma kham chua benh ban dau
    first_code = fields.Char('Code')
    # Noi Kham Chua benh ban dau
    address = fields.Text('Address')
    # kiem tra trai tuyen hay khong
    check_line = fields.Boolean('Check Line', default=False)

# Family Management

class DHAMPatientFamily(models.Model):
    _name = 'dham.patient.family'

    name = fields.Char(size=256, string='Name', help="Name" ,required=True)
    relation = fields.Char('Relation', required=1)
    mobile = fields.Char('Mobile')
    his_medical_illness = fields.Text('History of medical illness')
    patient_id = fields.Many2one('dham.patient', 'Patient', required=True, ondelete='cascade', index=True)

class DHAMPatient(models.Model):
    _name = 'dham.patient'
    _inherits = {
        'res.partner' : 'partner_id'
    }

    BLOOD_TYPE = [
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
        ('O', 'O'),
    ]

    MARITAL_STATUS = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ]

    last_check_in_time = fields.Datetime('Last Check In Time', track_visibility='onchange')
    married_status = fields.Selection(MARITAL_STATUS, 'Married Status', track_visibility='onchange')
    blood_type = fields.Selection(BLOOD_TYPE, string='Blood Type')
    insurrance_ids = fields.One2many('dham.patient.insurrance', 'patient_id', string='Patient ID', track_visibility='onchange')
    # don thuoc
    medicine_order_ids = fields.One2many('medicine.order', 'customer', 'Medicine Order', track_visibility='onchange')

    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, ondelete='cascade',
                                 help='Partner-related data of the hospitals', track_visibility='onchange')
    patient_user_id = fields.Many2one('res.users', string='Responsible Odoo User', track_visibility='onchange')
    family_ids = fields.One2many('dham.patient.family', 'patient_id', string='Family', track_visibility='onchange')
    patient_id = fields.Char('Patient ID', readonly=1, track_visibility='onchange')

    # Tien su benh
    tien_su_gia_dinh = fields.Char('Family history of medical illness', track_visibility='onchange')
    tien_can = fields.Char('Past medical and surgical history', track_visibility='onchange')
    di_ung_thuoc = fields.Char('Drug allergy', track_visibility='onchange')
    thuoc_la = fields.Char('Smoking', track_visibility='onchange')
    ruou = fields.Char('Alcolhol', track_visibility='onchange')
    the_thao = fields.Char('Exercises', track_visibility='onchange')
    tiem_ngua = fields.Char('Vaccination', track_visibility='onchange')


    _sql_constraints = [
        ('code_dham_medic_patient_userid_uniq', 'unique (patient_user_id)',
         "Selected 'Responsible' user is already assigned to another patient !"),
        ('dham_medic_patient_id_uniq', 'unique (patient_id)',
         "Patient ID already exist!")
    ]


    @api.constrains('day_of_birth')
    def _check_day_of_birth(self):
        for record in self:
            if record.day_of_birth:
                now = datetime.now()
                if datetime.strptime(record.day_of_birth, '%Y-%m-%d') > now:
                    raise ValidationError(_('Day of Birth must be less than now!'))

    @api.model
    def create(self, vals):
        res = super(DHAMPatient, self).create(vals)
        if self.env.context.get('from_external_center', False):
            try:
                code = self.env.ref('dham_medic.out_center_department').code
            except:
                code = '999'
        else:
            code = '000'
            EmployeeObj = self.env['hr.employee']
            emp_id = EmployeeObj.search([('user_id', '=', self._uid)], limit=1)
            if emp_id.department_id:
                center = emp_id.department_id.find_center()
                if center:
                    code = center.code or '000'
        code = code + self.env['ir.sequence'].next_by_code('patient.id.seq')
        res.write({'patient_id': code})
        return res

    @api.onchange('country_id')
    def _onchange_address_country_id(self):
        res = {'domain': {}}
        self.city_dropdown = False
        self.district = False
        self.ward = False
        if self.country_id:
            res['domain']['city_dropdown'] = [('country_id', '=', self.country_id.id)]
        return res

    @api.onchange('city_dropdown')
    def _onchange_address_city_dropdown(self):
        res = {'domain': {}}
        self.district = False
        self.ward = False
        if self.city_dropdown:
            if self.city_dropdown.city_type == 'city_in_province':
                res['domain']['ward'] = [('parent_code', '=', self.city_dropdown.code)]
                res['domain']['district'] = [('id', 'in', [])]
            else:
                res['domain']['district'] = [('parent_code', '=', self.city_dropdown.code)]
        return res

    @api.onchange('district')
    def _onchange_address_district(self):
        res = {'domain': {}}
        self.ward = False
        if self.district:
            res['domain']['ward'] = [('parent_code', '=', self.district.code)]
        return res