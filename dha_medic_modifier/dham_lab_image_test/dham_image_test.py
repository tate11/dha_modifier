# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

class DHAMXQ(models.Model):
    _name = 'xq.image.test'
    _inherit = 'base.image.test'

    TYPE_ID = 'dha_medic_modifier.medic_test_type_image_test'

    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_xq_img_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medic_xq_img_id', 'Consumable Supplies')

class DHAMSA(models.Model):
    _name = 'sa.image.test'
    _inherit = 'base.image.test'

    TYPE_ID = 'dha_medic_modifier.medic_test_type_echograph'

    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_sa_img_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medic_sa_img_id', 'Consumable Supplies')

class DHAMDTD(models.Model):
    _name = 'dtd.image.test'
    _inherit = 'base.image.test'

    TYPE_ID = 'dha_medic_modifier.medic_test_type_electrocardiogram'

    related_medical_bill = fields.Many2many('medic.medical.bill', 'medic_dtd_img_test_medical_bill_ref', 'test_id',
                                            'medical_bill_id', 'Related Medical Bills')
    # vat tu tieu hao
    consumable_supplies = fields.One2many('medic.consumable.supplies', 'medic_dtd_img_id', 'Consumable Supplies')
