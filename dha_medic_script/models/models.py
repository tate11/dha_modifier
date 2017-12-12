# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.modules import get_module_path
from odoo.addons.dha_medic_modifier.service.service_read_xlsx import ServiceReadXlsx

FIELD_NOR = ['name', 'state', 'assign_date', 'is_adding', 'result', 'note','customer', 'product_test', 'doctor_id', 'medical_bill_id', 'company_check_id']
FIELD_SPEC = ['image_res1', 'image_res2', 'image_res3',]



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
        self.copy_patient_field()
        self.get_patient_contract()
        return

    @api.model
    def get_patient_contract(self):
        Medical = self.env['medic.medical.bill']
        Patient = self.env['dham.patient']
        CONTRACT = self.env['res.partner.company.check']
        for con in CONTRACT.search([]):
            self.env.cr.execute(
                """
                SELECT customer 
                FROM medic_medical_bill
                WHERE company_check_id = %s;   
                """%(con.id)
            )
            customers = self.env.cr.fetchall()
            patients = Patient.search([('partner_id','in',customers)])
            con.write({'employees' : [(6,0,patients.ids)]})
            self.env.cr.commit()
        return True

    @api.model
    def copy_patient_field(self):
        Patients = self.env['dham.patient']
        MODELS = ['medic_test', 'xq_image_test','sa_image_test','dtd_image_test','medic_medical_bill']
        for model in MODELS:
            datas = []
            self.env.cr.execute("""
                select a.id, b.id from %s as a, dham_patient as b where a.customer = b.partner_id;
            """%model)
            datas = self.env.cr.fetchall()
            query = """
                UPDATE %s
                SET patient = CASE id
            """ % (model)
            for data in datas:
                query += """WHEN %s THEN %s """%(data[0],data[1])
            query += """ END WHERE id IN (%s)"""%(','.join([str(x[0]) for x in datas]))
            self.env.cr.execute(query)
        return True

    @api.model
    def move_image_test(self):
        FIELD_NOR_STR = ','.join(FIELD_NOR)
        switch_case = [
            (self.env.ref('dha_medic_modifier.medic_test_type_image_test').id, 'xq.image.test'),
            (self.env.ref('dha_medic_modifier.medic_test_type_echograph').id, 'sa.image.test'),
            (self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram').id, 'dtd.image.test'),
        ]
        external_center = self.env.ref('dha_medic_modifier.out_center_department').id
        for case in switch_case:
            records = self.env['medic.test'].search([('type', '=', case[0])])
            for record in records:
                data = {
                    'related_medical_bill': [(6, 0, record.related_medical_bill.ids or [])],
                    'type' : case[0],
                    'center_id' : external_center,
                }
                self.env.cr.execute("""
                    SELECT %s 
                    FROM medic_test
                    WHERE id=%s;
                """%(FIELD_NOR_STR,record.id))
                temp = self.env.cr.fetchall()
                data.update(dict(zip(FIELD_NOR, temp[0])))
                data.update(record.read(FIELD_SPEC)[0])
                res = self.env[case[1]].create(data)
                record.unlink()
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
            self.env.cr.commit()

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
