# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError



class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.depends('day_of_birth')
    def _compute_age(self):
        for record in self:
            if record.day_of_birth:
                now = datetime.now()
                delta = now - datetime.strptime(record.day_of_birth, '%Y-%m-%d')
                record.age = '%s years %s days' % (delta.days/365, delta.days % 365)

    # Mã Bệnh
    customer_id = fields.Char('Customer ID', readonly=1)
    # giới tính
    sex_id = fields.Many2one('res.partner.sex', 'Sex ID')
    # ngày khám cuối cùng
    last_check_in_time = fields.Datetime('Last Check In Time')
    day_of_birth = fields.Date('Day of Birth')
    age = fields.Char('Ages', compute=_compute_age)
    # Dân tộc
    ethnic_id = fields.Many2one('res.partner.ethnic', 'Ethnic ID')
    # quoc tich
    nationality_id = fields.Many2one('res.country', 'Nationality')
    cmnd_passport = fields.Char('CMND/PassPort')
    married_status = fields.Many2one('res.partner.married.status', 'Married Status')
    # tab gia dinh
    family_persons = fields.One2many('res.partner.family', 'partner_id', 'Family')
    # tab bao hiem
    insurrance_ids = fields.One2many('res.partner.insurrance', 'partner_id', string='Partner ID')
    # don thuoc
    medicine_order_ids = fields.One2many('medicine.order', 'customer', 'Medicine Order')

    # TESTs
    medic_lab_test_compute_ids = fields.Many2many('medic.test', 'Lab Tests', compute='_get_medic_test_ids')
    medic_image_test_compute_ids = fields.Many2many('medic.test', 'Image Tests', compute='_get_medic_test_ids')
    medic_test_ids = fields.One2many('medic.test', 'customer', 'Tests', domain=[('state','in',['new','processing'])])

    # tab kham cho cong ty
    company_medial_ids = fields.One2many('res.partner.company.check', 'company_id', 'Company Check')
    total_history = fields.Float('Check History', compute='_get_company_check_number')

    is_patient = fields.Boolean('Patient', default=False)

    def _get_company_check_number(self):
        CompanyCheck = self.env['res.partner.company.check']
        for record in self:
            record.total_history = len(CompanyCheck.search([('company_id', '=', record.id)]))

    def _get_medic_test_ids(self):
        MedictTest = self.env['medic.test']
        lab_type = [self.env.ref('dha_medic_modifier.medic_test_type_lab_test').id]
        image_type = [self.env.ref('dha_medic_modifier.medic_test_type_image_test').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_echograph').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram').id]
        for record in self:
            record.medic_lab_test_compute_ids = MedictTest.search(
                [('customer', '=', record.id), ('type', 'in', lab_type)])
            record.medic_image_test_compute_ids = MedictTest.search(
                [('customer', '=', record.id), ('type', 'in', image_type)])

    _sql_constraints = [
        ('cmnd_passport_uniq', 'unique (cmnd_passport)', _('CMND/PassPort must be unique !'))]




    @api.constrains('day_of_birth')
    def _check_day_of_birth(self):
        for record in self:
            if record.day_of_birth:
                now = datetime.now()
                if datetime.strptime(record.day_of_birth, '%Y-%m-%d') > now:
                    raise ValidationError(_('Day of Birth must be less than now!'))

    @api.multi
    def action_go_person_inv(self):
        for record in self:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': False,
                'context': {'default_partner_id': record.id, 'form_view_ref': 'account.invoice_form',
                            'default_order_type': 'medical'}
            }

    @api.multi
    def open_company_check_history(self):
        for record in self:
            CompanyCheck = self.env['res.partner.company.check']
            ids = CompanyCheck.search([('company_id', '=', record.id)]).ids
            action = self.env.ref('dha_medic_modifier.action_res_partner_company_check')
            action = action.read()[0]
            action['domain'] = [('id', 'in', ids)]
            return action

    @api.multi
    def action_go_select_package(self):
        for record in self:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.parse.package',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': False,
                'context': {'default_customer': record.id}
            }

    @api.model
    def create(self, vals):
        code = ''
        EmployeeObj = self.env['hr.employee']
        emp_id = EmployeeObj.search([('user_id', '=', self._uid)], limit=1)
        if emp_id.department_id:
            center = emp_id.department_id.find_center()
            if center:
                code += center.code or ''
            else:
                code += '000'
        now = datetime.now() + timedelta(hours=7)
        code = code + now.strftime('%Y%m%d') + self.env['ir.sequence'].next_by_code('customer.id.seq')
        vals['customer_id'] = code
        return super(ResPartner, self).create(vals)

    @api.model
    def _reset_seq_customer_id(self):
        now = datetime.now()
        vn_time = now + timedelta(hours=7)
        if vn_time.hour == 0:
            seq = self.env.ref('dha_medic_modifier.seq_medic_customer_id')
            if seq:
                seq.write({'number_next_actual': 1})
        return True


class PartnerSex(models.Model):
    _name = 'res.partner.sex'

    name = fields.Char('Name', required=True)


class PartnerEthnic(models.Model):
    _name = 'res.partner.ethnic'

    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('The ethnic group must be unique !'))]


class PartnerMarriedStatus(models.Model):
    _name = 'res.partner.married.status'

    name = fields.Char('Name', required=True)


class PartnerOccupation(models.Model):
    _name = "res.partner.occupation"

    name = fields.Char(string='Occupation', size=128, required=True)
    code = fields.Char(string='Code', size=128)

    _order = 'code'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The occupation name must be unique !')]


class PartnerFamily(models.Model):
    _name = "res.partner.family"

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', 'Partner ID', required=True, ondelete='cascade')
    person_id = fields.Many2one('res.partner', 'Related Customer', required=True)
    sex_id = fields.Many2one('res.partner.sex', 'Sex ID')
    day_of_birth = fields.Date('Day of Birth')
    relation = fields.Char('Relationship')
    mobile = fields.Char('Mobile')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.person_id:
            self.mobile = self.person_id.mobile or ''
            self.sex_id = self.person_id.sex_id or False
            self.day_of_birth = self.person_id.day_of_birth


class PartnerInsurrance(models.Model):
    _name = 'res.partner.insurrance'

    name = fields.Char('Number')
    type = fields.Many2one('res.partner.insurrance.type')
    join_date = fields.Date('Create Date')
    expiry_date = fields.Date('Expiry Date')
    partner_id = fields.Many2one('res.partner', 'Partner ID', required=True, ondelete='cascade')
    # ma kham chua benh ban dau
    first_code = fields.Char('Code')
    # Noi Kham Chua benh ban dau
    address = fields.Text('Address')
    # kiem tra trai tuyen hay khong
    check_line = fields.Boolean('Check Line', default=False)


class PartnerInsurranceLines(models.Model):
    _name = 'res.partner.insurrance.type'

    name = fields.Char('Name')


class PartnerCompanyCheck(models.Model):
    _name = 'res.partner.company.check'

    name = fields.Char('Name')
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done')], 'Status', default='new')
    package_ids = fields.Many2many('medic.package', 'medic_company_check_package_package_ref', 'wizard_id',
                                   'package_id', 'Packages', domain=[('type', '=', 'company')], required=1)
    company_id = fields.Many2one('res.partner', 'Company')
    employees = fields.Many2many('res.partner', 'company_check_res_partner_rel', 'company_check', 'partner_id',
                                 'Employees', required=1)
    start_time = fields.Date('Start Date')
    end_time = fields.Date('End Date')

    @api.onchange('company_id')
    def onchange_company_id(self):
        Partner = self.env['res.partner']
        if self.company_id:
            # employee_ids = Partner.search([('parent_id','=',self.company_id.id)])
            # self.employees = employee_ids
            return {'domain': {
                'employees': [('parent_id', '=', self.company_id.id)]
            }}

    @api.multi
    def action_validate(self):
        self.write({'state': 'processing'})
        for record in self:
            for emp in record.employees:

                Product = self.env['product.product']
                MedicalBill = self.env['medic.medical.bill']
                MedicTest = self.env['medic.test']
                Department = self.env['hr.department']
                products = Product

                product_list = record.package_ids.parse_multi_package()
                products += Product.browse(x[0] for x in product_list)
                if emp.sex_id:
                    products.filtered(lambda r: r.sex_id.id == emp.sex_id.id)

                center = Department._get_center_id(self._uid)

                product_medical = products.filtered(lambda r: r.type == 'service' and r.create_medical_bill == True)
                while len(product_medical) > 0:
                    same_type_pro = product_medical.filtered(
                        lambda r: r.buildings_type.id == product_medical[
                            0].buildings_type.id)

                    building = False
                    if center:
                        building = Department.search([('type', '=', 'buildings'), ('parent_id', '=', center.id),
                                                      ('buildings_type', '=', product_medical[0].buildings_type.id)],
                                                     limit=1)

                    new_bill = MedicalBill.create({
                        'customer': emp.id,
                        'invoice_id': self.id,
                        'service_ids': [(6, 0, same_type_pro.ids)],
                        'center_id': center.id,
                        'building_id': building.id or False,
                    })
                    product_medical -= same_type_pro
                    MedicalBill += new_bill
                MedicalBill.write({
                    'related_medical_bill_ids': [(6, 0, MedicalBill.ids or [])]
                })
                product_test = products.filtered(lambda r: r.type == 'service' and r.service_type)
                for pro in product_test:
                    MedicTest.create({
                        'type': pro.service_type.id,
                        'product_test': pro.id,
                        'customer': emp.id,
                        'related_medical_bill': [(6, 0, MedicalBill.ids)],
                    })
