# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

class MedicContract(models.Model):
    _inherit = 'medic.medical.bill'

    @api.model
    def get_patient_bill(self):
        customer_id = self._context.get('customer_id', False)
        buildings_type = self._context.get('buildings_type', False)
        doctor_id  = self._context.get('doctor_id', False)
        if not customer_id:
            exceptions.Warning('Please try again')

        company_check_id = int(self._context.get('company_check_id', False))
        if not company_check_id:
            exceptions.Warning('Please try again')

        bill_id = self.search([('customer_id','=',customer_id),('company_check_id','=',company_check_id)], limit=1)
        sub_treatment_id = bill_id.sub_treatment_ids.filtered(lambda st: st.buildings_type.id == buildings_type)
        treatmented = bill_id.sub_treatment_ids.filtered(lambda st: st.treatment_note and len(st.treatment_note)>0)
        return {
            'sex': bill_id.sex,
            'day_of_birth': bill_id.day_of_birth,
            'customer': bill_id.customer.name,
            'sub_treatment_id': sub_treatment_id.id,
            'parent_id': bill_id.id,
            'treatmented': treatmented.read(['buildings_type','doctor_id']),
        }