# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.modules import get_module_path
from odoo.addons.dha_medic_modifier.service.service_read_xlsx import ServiceReadXlsx

FIELD_NOR = ['name', 'state', 'assign_date', 'is_adding', 'image_res1', 'image_res2', 'image_res3', 'image_res4',
             'image_res5', 'image_res6',
             'result', 'note']
FIELD_SPEC = ['type', 'customer', 'center_id', 'product_test', 'doctor_id', 'doctor_assign', 'medical_bill_id',
              'company_check_id', 'result_template']


class dha_medic_script(models.Model):
    _name = 'dha_medic_script.dha_medic_script'

    name = fields.Char()

    @api.model
    def run_script(self):
        # self.fix_diagnose()
        # self.fix_diagnose_sub_treatment()
        # self.fix_cxk()
        # self.add_doctor()
        # self.fix_partner_id()

        # step by step
        # self.move_data_partner()
        # self.move_image_test()
        return

    @api.model
    def move_image_test(self):
        switch_case = [
            (self.env.ref('dha_medic_modifier.medic_test_type_image_test').id, 'xq.image.test'),
            (self.env.ref('dha_medic_modifier.medic_test_type_echograph').id, 'sa.image.test'),
            (self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram').id, 'dtd.image.test'),
        ]
        for case in switch_case:
            records = self.env['medic.test'].search([('type', '=', case[0]),('state','=','done')])
            for record in records:
                data = {'related_medical_bill': [(6, 0, record.related_medical_bill.ids or [])]}
                for field in FIELD_NOR:
                    data[field] = record[field]
                for field in FIELD_SPEC:
                    data[field] = record[field].id or False
                res = self.env[case[1]].create(data)
                self.env.cr.commit()

    @api.model
    def move_data_partner(self):
        Patient = self.env['dham.patient']
        for record in self.env['res.partner'].search([('is_patient', '=', True)]):
            Patient.create({
                'day_of_birth': record.day_of_birth,
                'patient_id': record.customer_id,
                'sex': record.sex,
                'married_status': record.married_status,
                'partner_id': record.id,
            })

    @api.model
    def fix_partner_id(self):
        self.env.cr.execute("""
            SELECT id 
            FROM res_partner
            WHERE LENGTH(customer_id) = 6;
        """)
        ids = self.env.cr.fetchall()
        partners = self.env['res.partner'].search([('id', 'in', ids)])
        for par in partners:
            par.write({'customer_id': ('999' + par.customer_id)})
        self.env.cr.commit()
        self.env.cr.execute("""
                    SELECT id 
                    FROM res_partner
                    WHERE customer_id LIKE '000%' or customer_id LIKE '004%';
                """)
        ids = self.env.cr.fetchall()
        partners = self.env['res.partner'].search([('id', 'in', ids)])
        for par in partners:
            par.write({'customer_id': ('999' + par.customer_id[3:])})
        return True

    @api.model
    def add_doctor(self):
        Medical = self.env['medic.medical.bill']
        SUB = self.env['medic.medical.sub.treatment']

        NOI = self.env.ref('dha_medic_modifier.khoa_nhi')
        MAT = self.env.ref('dha_medic_modifier.khoa_mat')
        TMH = self.env.ref('dha_medic_modifier.khoa_tai_mui_hong')
        RHM = self.env.ref('dha_medic_modifier.khoa_rang_ham_mat')
        DL = self.env.ref('dha_medic_modifier.khoa_da_lieu')

        module_path = get_module_path('dha_medic_script')
        file_path = module_path + '/static/file/ten_bac_si_2.xlsx'
        file = open(file_path, 'r')
        datas = (file.read())
        data_obj = ServiceReadXlsx().read_xls(datas)
        for data in data_obj:
            if data[0]:
                medical_id = Medical.search([('customer_id', '=', data[0])])
                if medical_id:
                    medical_id.write({'doctor_assign': 87})
                    if data[1]:
                        sub_id = SUB.search([('buildings_type', '=', NOI.id), ('parent_id', '=', medical_id.id)])
                        if sub_id:
                            sub_id.write({'doctor_id': int(data[1])})
                    if data[2]:
                        sub_id = SUB.search([('buildings_type', '=', MAT.id), ('parent_id', '=', medical_id.id)])
                        if sub_id:
                            sub_id.write({'doctor_id': int(data[2])})
                    if data[3]:
                        sub_id = SUB.search([('buildings_type', '=', TMH.id), ('parent_id', '=', medical_id.id)])
                        if sub_id:
                            sub_id.write({'doctor_id': int(data[3])})
                    if data[4]:
                        sub_id = SUB.search([('buildings_type', '=', RHM.id), ('parent_id', '=', medical_id.id)])
                        if sub_id:
                            sub_id.write({'doctor_id': int(data[4])})
                    # if data[5]:
                    #     sub_id = SUB.search([('buildings_type', '=', DL.id),('parent_id','=',medical_id.id)])
                    #     if sub_id:
                    #         sub_id.write({'doctor_id': int(data[5])})

    @api.model
    def fix_diagnose(self):
        Medical = self.env['medic.medical.bill'].sudo()
        medical_ids = Medical.search([('diagnose_icd', '!=', False)])
        index = 1
        for medical_id in medical_ids:
            note = medical_id.treatment_note or ''
            for icd in medical_id.diagnose_icd.mapped('name'):
                note = icd + '\n' + note
            medical_id.write({
                'treatment_note': note,
                'diagnose_icd': [(6, 0, [])],
            })
            print str(index)
            index += 1

    @api.model
    def fix_diagnose_sub_treatment(self):
        Medical = self.env['medic.medical.bill'].sudo()
        SubTreatement = self.env['medic.medical.sub.treatment'].sudo()
        sub_ids = SubTreatement.search([('diagnose', '!=', False)])
        for sub in sub_ids:
            note = sub.treatment_note or ''
            note = sub.diagnose + '\n' + note
            sub.write({
                'treatment_note': note,
                'diagnose': False
            })

    @api.model
    def fix_cxk(self):
        Medical = self.env['medic.medical.bill'].sudo()
        SubTreatement = self.env['medic.medical.sub.treatment'].sudo()
        Noi = self.env.ref('dha_medic_modifier.khoa_nhi')

        medical_ids = Medical.search([('state', 'in', ('processing', 'done'))])
        for medical_id in medical_ids:
            sub_cxk_id = SubTreatement.search([('parent_id', '=', medical_id.id), ('buildings_type', '=', False)])
            sub_noi_id = SubTreatement.search([('parent_id', '=', medical_id.id), ('buildings_type', '=', Noi.id)])

            if sub_cxk_id and sub_noi_id and len(sub_cxk_id) == 1:
                sub_noi_id.write({
                    'co_xuong_khop': sub_cxk_id.treatment_note or '',
                })
                sub_cxk_id.unlink()
            elif len(sub_cxk_id) > 1:
                print '%s' % (medical_id.name)
