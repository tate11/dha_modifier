# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import datetime


class MedicMedicalBill(models.Model):
    _name = 'medic.medical.bill'
    _inherit = 'mail.thread'
    _description = 'Medical Bill'
    _order = 'id desc'


    name = fields.Char('Number', default=lambda self: self.env['ir.sequence'].next_by_code('medic.medical.bill'))
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done')], default='new',
                             string='Status', track_visibility='onchange')
    process_date = fields.Datetime('Processing Date')
    done_date = fields.Datetime('Done Date')

    customer = fields.Many2one('res.partner', 'Customer', track_visibility='onchange')
    customer_name = fields.Char( 'Name', related='customer.name', readonly=1)
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    customer_parent_id = fields.Many2one('res.partner', string='Customer Company ID', related='customer.parent_id', readonly=1, store=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='customer.sex', readonly=0, track_visibility='onchange')
    description = fields.Char(string='Description', related='customer.description')
    check_vip = fields.Boolean('Check VIP', compute='_compute_check_vip')
    customer_image_small = fields.Binary('Customer Image', related='customer.image_small', readonly=1)

    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=0, track_visibility='onchange')
    type = fields.Selection([('company','Company'),('person','Person')], 'Type', default='person')
    invoice_id = fields.Many2one('account.invoice', 'Invoice ID')

    center_id = fields.Many2one('hr.department', 'Center', readonly=1, track_visibility='onchange')
    building_id = fields.Many2one('hr.department', 'Building', track_visibility='onchange')
    room_id = fields.Many2one('hr.department', 'Room', readonly=1, track_visibility='onchange')
    doctor_assign = fields.Many2one('hr.employee', 'Physician', track_visibility='onchange')

    #track tao ra tu goi kham cong ty
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', copy=False, readonly=1)


    # related Medical Bills
    related_medical_bill_ids = fields.Many2many('medic.medical.bill', 'medic_medical_bill_medic_medical_bill_ids_rel',
                                                'id1', 'id2', 'Related Medical Bills')

    # don thuoc
    medicine_orders = fields.One2many('medicine.order', 'medical_id', 'Medicine Bill')

    # tab sinh hieu (Vital sign)
    # huyet ap
    blood_pressure = fields.Char('Blood Pressure (mmHg)', track_visibility='onchange')
    blood_pressure_max = fields.Char('Blood Pressure Max (mmHg)', track_visibility='onchange')

    # mach
    pulse = fields.Char('Pulse (per min)', track_visibility='onchange')
    # nhiet do
    temperatures = fields.Char('Temperatures', track_visibility='onchange')
    # nhip tho
    pace_of_breathe = fields.Char('Pace of Breathe (per min)', track_visibility='onchange')
    height = fields.Float('Height (Cm)', track_visibility='onchange')
    weight = fields.Float('Weight (Kg)', track_visibility='onchange')
    bmi = fields.Char('BMI', compute='_compute_bmi', digit=2)
    # di ung thuoc
    allergy = fields.Many2many('product.product', 'medical_bill_product_product_rel', 'medical_id', 'product_id',
                               'Allergy')
    special = fields.Text('Special', track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    # tab Dieu tri
    # trieu chung
    prognostic = fields.Text('Prognostic', track_visibility='onchange')
    reason = fields.Text('Reason', track_visibility='onchange')
    # chuan doan
    diagnose_icd = fields.Many2many('medic.diseases', 'medical_bill_diseases_rel', 'medical_bill_id', 'diseases_id',
                                    'Diagnose ICD')
    diagnose = fields.Char('Diagnose', track_visibility='onchange')
    phan_loai = fields.Many2one('treatement.classify', 'Classify')
    treatment_note = fields.Text('Note', track_visibility='onchange')
    treatment_template = fields.Many2many('treatment.template', relation='medical_bill_treatment_template_rel', col1='medical_id', col2='template_id', string='Template', domain=[('type','=',False)])
    #chuan doan phu
    sub_treatment_ids = fields.One2many('medic.medical.sub.treatment','parent_id', 'Sub Treatments')

    # tab xet nghiem
    medic_test_ids = fields.One2many('medic.test', 'medical_bill_id', 'Tests')
    medic_lab_test_compute_ids = fields.Many2many('medic.test', 'Lab Tests', compute='_get_medic_test_ids')
    medic_xq_image_compute_ids = fields.Many2many('xq.image.test', 'Image Tests', compute='_get_medic_test_ids')
    medic_sa_image_compute_ids = fields.Many2many('sa.image.test', 'Echograph Tests', compute='_get_medic_test_ids')
    medic_dtd_image_compute_ids = fields.Many2many('dtd.image.test', 'Electrocardiogram Tests', compute='_get_medic_test_ids')

    # tab Appoint
    appoint_ids = fields.One2many('medic.appoint', 'medical_bill_id', 'Appoint')

    # services
    service_ids = fields.Many2many('product.product', 'medic_medical_bill_product_product_rel', 'medical_bill_id',
                                   'product_id', 'Services')
    adding_service_ids = fields.Many2many('product.product', 'medic_medical_bill_adding_product_product_rel', 'medical_bill_id',
                                   'product_id', 'Adding Services')
    #Test Done Percent
    done_percent = fields.Char('Tests Done', compute='_compute_test_done_status')

    #Vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medical_id', 'Consumable Supplies')
    #de nghi
    de_nghi = fields.Text('Suggestion')
    phan_loai_char = fields.Char('Phan Loai', compute='_compute_phanl_loai_char')

    @api.one
    @api.depends('phan_loai')
    def _compute_phanl_loai_char(self):
        a = [x.id for x in (self.env.ref('dha_medic_modifier.%s'%(r)) for r in ['loai_1', 'loai_2', 'loai_3'])]
        b = [x.id for x in (self.env.ref('dha_medic_modifier.%s'%(r)) for r in ['loai_4', 'loai_5'])]
        for record in self:
            if record.phan_loai.id in a:
                record.phan_loai_char = '1'
            elif record.phan_loai.id in b:
                record.phan_loai_char = '0'
    
    @api.depends('height', 'weight')
    def _compute_bmi(self):
        for record in self:
            if record.height:
                record.bmi = round(record.weight / ((record.height/100)**2), 2)
            else:
                record.bmi = 0

    @api.onchange('treatment_template')
    def onchange_treatment_template(self):
        self.treatment_note = False
        if self.treatment_template:
            template_body = ''
            for body in self.treatment_template:
                template_body += '\n' + body.template
            self.treatment_note = template_body

    @api.multi
    def _compute_check_vip(self):
        for record in self:
            if record.customer:
                if record.customer.category_id.filtered(lambda r: r.name == 'VIP'):
                    record.check_vip = True
    @api.multi
    def _compute_test_done_status(self):
        MedicTest = self.env['medic.test']
        XQTest = self.env['xq.image.test']
        SATest = self.env['sa.image.test']
        DTDTest = self.env['dtd.image.test']
        Ms = [MedicTest, XQTest, SATest, DTDTest]
        for record in self:
            domain = [('related_medical_bill', 'in', [record.id])]
            domain_done = [('related_medical_bill', 'in', [record.id]), ('state', '=', 'done')]
            total = 0
            done = 0
            for m in Ms:
                total += m.search_count(domain)
                done += m.search_count(domain_done)
            record.done_percent = '%s / %s'%(str(done), str(total))

    def _get_medic_test_ids(self):
        MedicTest  = self.env['medic.test']
        XQTest = self.env['xq.image.test']
        SATest = self.env['sa.image.test']
        DTDTest = self.env['dtd.image.test']
        for record in self:
            domain = [('related_medical_bill', 'in', [record.id])]
            record.medic_lab_test_compute_ids = MedicTest.search(domain)
            record.medic_xq_image_compute_ids = XQTest.search(domain)
            record.medic_sa_image_compute_ids = SATest.search(domain)
            record.medic_dtd_image_compute_ids = DTDTest.search(domain)

    @api.multi
    def action_processing(self):
        data = {'state': 'processing','process_date' : fields.Datetime.now()}
        if not self.doctor_assign:
            emp = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1).id or False
            data['doctor_assign'] = emp
        if self.type == 'company':
            data['sub_treatment_ids']  = self.parse_sub_treatment()
        self.write(data)

    @api.model
    def parse_sub_treatment(self):
        res = []
        khoas = ['khoa_nhi', 'khoa_mat', 'khoa_tai_mui_hong', 'khoa_rang_ham_mat', 'khoa_da_lieu', 'khoa_ngoai',
                 'khoa_san']
        for khoa in khoas:
            if khoa == 'khoa_san' and self.sex == 'male':
                continue
            res.append((0, 0, {'buildings_type': self.env.ref('dha_medic_modifier.' + khoa).id,
                               'doctor_id': False,
                               'type': 'company',
                               }))
        return res

    @api.multi
    def action_done(self):
        self.write({'state': 'done','done_date' : fields.Datetime.now()})
        self.consumable_supplies._apply_stock_(self.center_id)

    @api.onchange('service_ids')
    def onchange_service_ids(self):
        ConsumableObj = self.env['medic.consumable.supplies']
        self.consumable_supplies = False
        datas = ConsumableObj._get_product_qty_data(self.service_ids)
        for data in datas:
            self.consumable_supplies += self.consumable_supplies.new(data)

    @api.model
    def create(self, vals):
        res = super(MedicMedicalBill, self).create(vals)
        ConsumableObj = self.env['medic.consumable.supplies']
        if not 'consumable_supplies' in vals and 'service_ids' in vals:
            datas = res.consumable_supplies._get_product_qty_data(res.service_ids)
            for data in datas :
                data['medical_id'] = res.id
                ConsumableObj.create(data)
        return res

    @api.multi
    def action_reset_to_processing(self):
        self.write({'state' : 'processing'})

    @api.multi
    def action_quick_fill_treatment(self):
        for record in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid), ('department_id', '!=', False)])
            if employee and employee.department_id:
                if employee.department_id.buildings_type:
                    matched_sub = record.sub_treatment_ids.filtered(lambda r: r.buildings_type.id == employee.department_id.buildings_type.id)
                    if matched_sub:
                        return {
                            'type': 'ir.actions.act_window',
                            'name': 'Treatment',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'res_model': 'medic.medical.sub.treatment',
                            'res_id' : matched_sub.id,
                            'flags': {'initial_mode': 'edit'},
                            'target': 'new',
                        }
                    else:
                        raise UserError (_('Have no treatment matched your building!'))
                else:
                    raise UserError(_('Wrong department!'))
            else:
                raise UserError(_('Please config your department first!'))

class MedicSubTreatment(models.Model):
    _name = 'medic.medical.sub.treatment'
    _description = 'Medical Sub Treatement'

    @api.model
    def _get_default_building_type(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self._uid), ('department_id', '!=', False)])
        if employee:
            building = employee.department_id.find_building()
            if building and building.buildings_type:
                return building.buildings_type.id

    @api.model
    def _get_default_doctor(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
        return employee.id

    @api.model
    def default_get(self, fields):
        vals = super(MedicSubTreatment, self).default_get(fields)
        try:
            loai = self.env.ref('dha_medic_modifier.loai_1').id
        except:
            loai = False
        default_field = ['phan_loai', 'phan_loai_tuan_hoan', 'phan_loai_ho_hap', 'phan_loai_tieu_hoa',
                         'phan_loai_co_xuong_khop',
                         'phan_loai_than_tiet_nieu', 'phan_loai_than_kinh', 'phan_loai_tam_than', 'phan_loai_noi_tiet']
        res_field = ['tuan_hoan','ho_hap','tieu_hoa','than_tiet_nieu','co_xuong_khop','than_kinh','tam_than','noi_tiet']
        for field in default_field:
            vals[field] = loai
        for field in res_field:
            vals[field] = 'Bình thường'
        return vals

    name = fields.Char('Name')
    diagnose_icd = fields.Many2many('medic.diseases', 'medical_sub_treatment_diseases_rel', 'sub_treatment_id', 'diseases_id',
                                    'Diagnose ICD')
    diagnose = fields.Char('Diagnose')
    de_nghi = fields.Char('Suggestion')
    type = fields.Selection([('company','Company'),('person','Person')], 'Type', default='person')

    phan_loai = fields.Many2one('treatement.classify', 'Classify')
    treatment_note = fields.Text('Note')
    
    doctor_id = fields.Many2one('hr.employee', 'Physician', default=_get_default_doctor)
    doctor_ids = fields.Many2many('hr.employee', 'sub_treatment_hr_employee_rel', 'company_check', 'emp_id', 'Doctors', compute='_compute_doctor_ids')
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', related='parent_id.company_check_id', readonly=1)


    treatment_template = fields.Many2many('treatment.template', relation='sub_treatement_treatment_template_rel', col1='treatement_id', col2='template_id', string='Template', domain=[('type','=',False)])

    parent_id = fields.Many2one('medic.medical.bill', 'Parent Id', required=1, ondelete='cascade')

    buildings_type = fields.Many2one('hr.department.building.type', 'Building', default=_get_default_building_type)
    di_tat_bam_sinh = fields.Char('Birth Defects')
    
    #Noi khoa
    tuan_hoan = fields.Char('Cardiovascular System')
    phan_loai_tuan_hoan = fields.Many2one('treatement.classify', 'Classify')
    th_tmp = fields.Many2one('treatment.template', 'TH Template', domain=[('type','=','th')])

    ho_hap = fields.Char('Respiratory System')
    phan_loai_ho_hap = fields.Many2one('treatement.classify', 'Classify')
    hh_tmp = fields.Many2one('treatment.template', 'HH Template', domain=[('type','=','hh')])

    tieu_hoa = fields.Char('Gastroinestinal System')
    phan_loai_tieu_hoa = fields.Many2one('treatement.classify', 'Classify')
    ti_h_tmp = fields.Many2one('treatment.template', 'TiH Template', domain=[('type','=','ti_h')])

    than_tiet_nieu = fields.Char('Genito-urinary System')
    phan_loai_than_tiet_nieu = fields.Many2one('treatement.classify', 'Classify')
    ttn_tmp = fields.Many2one('treatment.template', 'TTN Template', domain=[('type','=','ttn')])

        # co xuong khop
    co_xuong_khop = fields.Char('Musculoskeletal System')
    phan_loai_co_xuong_khop = fields.Many2one('treatement.classify', 'Classify')
    cxk_tmp = fields.Many2one('treatment.template', 'CXK Template', domain=[('type','=','cxk')])
    
    than_kinh = fields.Char('Central Nervous System')
    phan_loai_than_kinh = fields.Many2one('treatement.classify', 'Classify')
    tk_tmp = fields.Many2one('treatment.template', 'TK Template', domain=[('type','=','tk')])

    tam_than = fields.Char('Psychiatric System')
    phan_loai_tam_than = fields.Many2one('treatement.classify', 'Classify')
    tt_tmp = fields.Many2one('treatment.template', 'TT Template', domain=[('type','=','tt')])

    noi_tiet = fields.Char('Endocrinologist')
    phan_loai_noi_tiet = fields.Many2one('treatement.classify', 'Classify')
    nt_tmp = fields.Many2one('treatment.template', 'NT Template', domain=[('type', '=', 'nt')])


    check_nhi = fields.Boolean('Check Nhi', compute='_compute_check_show_result')

    #Mat
    phai_ko_kinh = fields.Char('Right w/o glass')
    phai_co_kinh = fields.Char('Right w glass')
    trai_co_kinh = fields.Char('Left w glass')
    trai_ko_kinh = fields.Char('Left w/o glass')
    check_mat = fields.Boolean('Check Mat', compute='_compute_check_show_result')

    #tai mui hong
    trai_noi_thuong = fields.Char('Left Air Transmission')
    trai_noi_tham = fields.Char('Left Bone Transmission')
    phai_noi_thuong = fields.Char('Right Air Transmission')
    phai_noi_tham = fields.Char('Right Bone Transmission')
    check_tai_mui_hong = fields.Boolean('Check Tai Mui Hong', compute='_compute_check_show_result')

    # rang ham mat
    ham_tren = fields.Char('Upper Jaw')
    ham_duoi = fields.Char('Below Jaw')
    check_rang_ham_mat = fields.Boolean('Check Rang Ham Mat', compute='_compute_check_show_result')

    #Da lieu
    check_da_lieu = fields.Boolean('Check Da Lieu', compute='_compute_check_show_result')

    #khoa ngoai
    check_ngoai = fields.Char('Check Ngoai', compute='_compute_check_show_result')

    #khoa san
    check_san = fields.Char('Check San', compute='_compute_check_show_result')

    @api.onchange('th_tmp')
    def onchange_th_tmp(self):
        self.tuan_hoan = self.th_tmp.template or ''

    @api.onchange('hh_tmp')
    def onchange_hh_tmp(self):
        self.ho_hap = self.hh_tmp.template or ''

    @api.onchange('ti_h_tmp')
    def onchange_ti_h_tmp(self):
        self.tieu_hoa = self.ti_h_tmp.template or ''

    @api.onchange('ttn_tmp')
    def onchange_ttn_tmp(self):
        self.than_tiet_nieu = self.ttn_tmp.template or ''

    @api.onchange('cxk_tmp')
    def onchange_cxk_tmp(self):
        self.co_xuong_khop = self.cxk_tmp.template or ''

    @api.onchange('tk_tmp')
    def onchange_tk_tmp(self):
        self.than_kinh = self.tk_tmp.template or ''

    @api.onchange('tt_tmp')
    def onchange_tt_tmp(self):
        self.tam_than = self.tt_tmp.template or ''

    @api.onchange('nt_tmp')
    def onchange_nt_tmp(self):
        self.noi_tiet = self.nt_tmp.template or ''

    @api.depends('buildings_type')
    def _compute_check_show_result(self):
        for record in self:
            record.check_nhi = False
            record.check_mat = False
            record.check_tai_mui_hong = False
            record.check_rang_ham_mat = False
            record.check_da_lieu = False
            record.check_ngoai = False
            record.check_san = False
            try:
                if record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_nhi').id:
                    record.check_nhi = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_mat').id:
                    record.check_mat = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_tai_mui_hong').id:
                    record.check_tai_mui_hong = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_rang_ham_mat').id:
                    record.check_rang_ham_mat = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_da_lieu').id:
                    record.check_da_lieu = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_ngoai').id:
                    record.check_ngoai = True
                elif record.buildings_type.id == self.env.ref('dha_medic_modifier.khoa_san').id:
                    record.check_san = True
            except:
                pass

    @api.onchange('treatment_template')
    def onchange_treatment_template(self):
        self.treatment_note = False
        if self.treatment_template:
            template_body = ''
            for body in self.treatment_template:
                template_body += '\n' + body.template
            self.treatment_note = template_body

    @api.multi
    def write(self, vals):
        if self.env.context.get('auto_fill_doctor', False):
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
            if employee:
                vals['doctor_id'] = employee.id
        return super(MedicSubTreatment, self).write(vals)

class TreatmentTemplate(models.Model):
    _name = 'treatment.template'

    name = fields.Char('Name', required=1)
    template = fields.Text('Template', required=1)
    type = fields.Selection([
        ('th','Cardiovascular System'),('hh','Respiratory System'),
        ('ti_h', 'Gastroinestinal System'),('ttn','Genito-urinary System'),
        ('cxk', 'Musculoskeletal System'), ('tk', 'Central Nervous System'),
        ('tt', 'Psychiatric System'),('nt','Endocrinologist')
    ], string='Type', default=False)

class TreatementClassify(models.Model):
    _name = 'treatement.classify'
    
    name = fields.Char('Name', required=1)
    description = fields.Char('Description')
    code = fields.Char('Code')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            name += (' ( ' + record.description + ' )') if record.description else ''
            res.append((record.id, name))
        return res

class ResPartner(models.Model):
    _inherit = 'res.partner'

    medical_bill_ids = fields.One2many('medic.medical.bill', 'customer', 'Medical Bill')
    medical_bill_domain_ids = fields.One2many('medic.medical.bill', 'customer', 'Medical Bill', domain=[('state','in',['new','processing'])])