# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime

class MedicContract(models.Model):
    _inherit = 'medic.medical.bill'

    @api.model
    def get_patient_bill(self):
        record_id = False
        view_id = False
        model = False
        name = ''
        buildings_type = self._context.get('buildings_type', False)
        doctor_id = self._context.get('doctor_id', False)
        emplyee_id = self.env['hr.employee'].browse(doctor_id)

        customer_id = self._context.get('customer_id', False)
        if not customer_id:
            exceptions.Warning('Please try again')

        company_check_id = int(self._context.get('company_check_id', False))
        if not company_check_id:
            exceptions.Warning('Please try again')

        bill_id = self.search([('customer_id', '=', customer_id), ('company_check_id', '=', company_check_id)], limit=1)
        if emplyee_id.department_id:
            if emplyee_id.department_id.type == 'buildings':
                view_id = self.env.ref('dham_doctor_interface.medic_medic_medical_sub_treatment_form').id
                record_id = bill_id.sub_treatment_ids.filtered(lambda st: st.buildings_type.id == buildings_type)
                model = 'medic.medical.sub.treatment'
                name = emplyee_id.department_id.buildings_type.name
            elif emplyee_id.department_id.type == 'center':
                view_id = self.env.ref('dham_doctor_interface.medic_medic_medical_bill_form').id
                record_id = bill_id
                model = 'medic.medical.bill'
                name = 'Vital Sign'

        not_treatmented = bill_id.sub_treatment_ids.filtered(lambda st: not (st.treatment_note and st.treatment_note != ''))
        treatmented = bill_id.sub_treatment_ids.filtered(lambda st: st.id not in not_treatmented.ids)

        return {
            'model': model,
            'sex': bill_id.sex,
            'day_of_birth': bill_id.day_of_birth,
            'time_tiep_nhan': bill_id.time_tiep_nhan,
            'time_tra_lai': bill_id.time_tra_lai,
            'customer': bill_id.customer.name,
            'record_id': record_id.id,
            'name': _(name),
            'parent_id': bill_id.id,
            'treatmented': treatmented.read(['buildings_type', 'doctor_id', 'treatment_note']),
            'not_treatmented': not_treatmented.read(['buildings_type', 'doctor_id', 'treatment_note']),
            'view_id': view_id,
        }

    @api.model
    def patient_check_in(self):
        customer_id = self._context.get('customer_id', False)
        if not customer_id:
            exceptions.Warning('Please try again')

        company_check_id = int(self._context.get('company_check_id', False))
        if not company_check_id:
            exceptions.Warning('Please try again')

        bill_id = self.search([('customer_id', '=', customer_id), ('company_check_id', '=', company_check_id)], limit=1)
        bill_id.write({'time_tiep_nhan': datetime.today()})

        return {
            'sex': bill_id.sex,
            'day_of_birth': bill_id.day_of_birth,
            'customer': bill_id.customer.name,
            'time_tiep_nhan': bill_id.time_tiep_nhan,
            'time_tra_lai': bill_id.time_tra_lai,
            'treatmented': bill_id.sub_treatment_ids.read(['buildings_type', 'doctor_id', 'treatment_note']),
            'not_treatmented': [],
            'success': True,
            'action': 'check in',
        }

    @api.model
    def patient_check_out(self):
        customer_id = self._context.get('customer_id', False)
        if not customer_id:
            exceptions.Warning('Please try again')

        company_check_id = int(self._context.get('company_check_id', False))
        if not company_check_id:
            exceptions.Warning('Please try again')

        bill_id = self.search([('customer_id', '=', customer_id), ('company_check_id', '=', company_check_id)], limit=1)
        bill_id.write({'time_tra_lai': datetime.today()})
        not_treatmented = bill_id.sub_treatment_ids.filtered(lambda st: not (st.treatment_note and st.treatment_note != ''))
        treatmented = bill_id.sub_treatment_ids.filtered(lambda st: st.id not in not_treatmented.ids)

        return {
            'sex': bill_id.sex,
            'day_of_birth': bill_id.day_of_birth,
            'customer': bill_id.customer.name,
            'time_tiep_nhan': bill_id.time_tiep_nhan,
            'time_tra_lai': bill_id.time_tra_lai,
            'treatmented': treatmented.read(['buildings_type', 'doctor_id', 'treatment_note']),
            'not_treatmented': not_treatmented.read(['buildings_type', 'doctor_id', 'treatment_note']),
            'success': False,
            'action': 'check out',
        }

    @api.model
    def get_patient_list(self):
        company_check_id = int(self._context.get('company_check_id', False))
        if not company_check_id:
            exceptions.Warning('Please try again')
        bill_ids = self.search(['|',('time_tiep_nhan','!=',False),('time_tra_lai','!=',False),('company_check_id', '=', company_check_id)])
        return bill_ids.read(['customer','customer_id','time_tiep_nhan','time_tra_lai'])