# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicDiseases(models.Model):
    _name = 'medic.diseases'
    _order = 'id desc'


    name = fields.Char('Name')
    code = fields.Char('Code')
    category = fields.Many2one('medic.diseases.category', 'Diseases Category')
    description = fields.Text('Description')

class MedicDiseasesCategory(models.Model):
    _name = 'medic.diseases.category'

    name = fields.Char('Name')
    parent_ctg = fields.Many2one('medic.diseases.category', 'Parent Category')