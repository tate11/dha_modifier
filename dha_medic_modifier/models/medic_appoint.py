# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicAppoint(models.Model):
    _name = 'medic.appoint'
    _inherit = 'mail.thread'
    _order = 'id desc'


    @api.model
    def get_default_doctor(self):
        Employee = self.env['hr.employee']
        return Employee.search([('user_id','=',self._uid)], limit=1).id or False


    name = fields.Char('Number', readonly=1, default='/')
    state = fields.Selection([('new', 'New'), ('validate', 'Validated')], 'Status', default='new', track_visibility='onchange')

    patient = fields.Many2one('dham.patient', 'Patient', track_visibility='onchange', index=1)
    customer = fields.Many2one('res.partner', 'Customer', track_visibility='onchange')
    customer_id = fields.Char(string='Customer ID', related='patient.patient_id', readonly=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='patient.sex', readonly=1)

    day_of_birth = fields.Date(string='Day of Birth', related='patient.day_of_birth', readonly=1)

    doctor_assign = fields.Many2one('hr.employee', 'Assigned By', track_visibility='onchange')
    assign_date = fields.Datetime('Appoint Date', default=lambda *a: datetime.datetime.now(), track_visibility='onchange')

    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    line_ids = fields.One2many('medic.appoint.line', 'parent_id', 'Lines', track_visibility='onchange')

    package_ids = fields.Many2many('medic.package', 'medic_appoint_package_ref', 'appoint_id', 'package_id', 'Packages', domain=[('type', '=', 'person')])

    @api.onchange('package_ids')
    def onchange_package_ids(self):
        for record in self:
            record.line_ids = False
            product_list = record.package_ids.parse_multi_package()
            for product in product_list:
                record.line_ids += record.line_ids.new({
                    'product_id': product[0],
                    'qty': 1,
                })

    @api.multi
    def action_validate(self):
        self.write({'state': 'validate'})
        Receive = self.env['dham.patient.recieve']
        ReceiveLine = self.env['dham.patient.recieve.line']
        line_ids = []
        for line in self.line_ids:
            line_ids.append({
                'product_id': line.product_id.id,
                'price_unit': line.product_id.lst_price,
                'name': line.product_id.description or line.product_id.name,
                'product_uom_qty': 1,
                'product_uom': line.product_id.uom_id.id or False,
                'tax_id': line.product_id.taxes_id.ids or [],
            })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'dham.patient.recieve',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': False,
            'context': {'default_patient': self.patient.id, 'default_medical_bill_id': self.medical_bill_id .id,
                        'default_line_ids': line_ids, 'default_doctor_assign': self.doctor_assign.id
               , 'default_center_id' : self.medical_bill_id.center_id.id or False,'no_onchange_package' : True}
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medic.appoint.seq')
        return super(MedicAppoint, self).create(vals)

class MedicAppointLine(models.Model):
    _name = 'medic.appoint.line'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    qty = fields.Float('Quantity', default=1.0)
    parent_id = fields.Many2one('medic.appoint', 'Appoint')
