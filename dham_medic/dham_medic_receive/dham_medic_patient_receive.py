# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import odoo.addons.decimal_precision as dp

class DHAMReceive(models.Model):
    _name = 'dham.patient.recieve'
    _order = 'id desc'
    _inherits = {
        'sale.order' : 'sale_order_id'
    }

    @api.model
    def _get_center_id(self):
        try:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if employee_id:
                if employee_id[0].department_id:
                    return employee_id[0].department_id.find_center()
        except:
            pass
        return False

    @api.depends('patient_id')
    def _compute_insurrance(self):
        for record in self:
            if record.patient_id:
                record.insurrance_ids = record.patient_id.insurrance_ids

    name = fields.Char('Receive Number')
    receive_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('canceled','Canceled')
    ], readonly=1, index=1, string='Status', default='draft')

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', required=1, ondelete='cascade', index=1, readonly=1)
    patient_id = fields.Many2one('dham.patient', 'Patient')
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='patient_id.sex', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='patient_id.day_of_birth', readonly=1)
    mobile = fields.Char('Mobile', related='patient_id.mobile', readonly=1)
    insurrance_ids = fields.Many2many('res.partner.insurrance', compute='_compute_insurrance', string='Insurrance',
                                      readonly=1)
    # ly do
    reason = fields.Text('Reason')
    # trieu chung
    prognostic = fields.Text('Prognostic')

    # PHong Kham

    center_id = fields.Many2one('hr.department', 'Center', default=_get_center_id, domain=[('type', '=', 'center')],
                                track_visibility='onchange')
    building_id = fields.Many2one('hr.department', 'Building', domain=[('type', '=', 'buildings')],
                                  track_visibility='onchange')
    room_id = fields.Many2one('hr.department', 'Room', domain=[('type', '=', 'room')], track_visibility='onchange')

    doctor_assign = fields.Many2one('hr.employee', 'Assigned By', track_visibility='onchange')
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Order')
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', copy=False)
    package_ids = fields.Many2many('medic.package', 'medic_patient_receive_package_ref', 'receive_id', 'package_id',
                                   'Packages', domain=[('type', '=', 'person')])

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('patient.receive.seq')
        res = super(DHAMReceive, self).create(vals)
        return res

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        self.partner_id = self.patient_id and self.patient_id.partner_id.id or False
        if self.env.context.get('default_contract_adding_services', False):
            Contract = self.env['res.partner.company.check'].sudo().search(
                [('id', '=', self.env.context.get('default_contract_adding_services'))])
            if self.patient_id and Contract:
                self.medical_bill_id = self.env['medic.medical.bill'].search(
                    [('company_check_id', '=', Contract.id), ('customer', '=', self.patient_id.id)]).id or False
            if Contract:
                return {
                    'domain': {
                        'patient_id': [('id', 'in', Contract.employees.ids)]
                    }
                }

    @api.onchange('room_id')
    def onchange_room_id(self):
        if self.room_id:
            return {
                'domain': {
                    'doctor_assign': [('department_id', '=', self.room_id.id)]
                }
            }

    @api.onchange('center_id', 'building_id')
    def onchange_center_building(self):
        res = {
            'domain': {}
        }
        if self.center_id:
            res['domain']['building_id'] = [('parent_id', '=', self.center_id.id)]
        if self.building_id:
            res['domain']['room_id'] = [('parent_id', '=', self.building_id.id)]
        return res

    @api.onchange('package_ids')
    def onchange_package_ids(self):
        if 'no_onchange_package' in self.env.context:
            return
        ProductObj = self.env['product.product']

        for record in self:
            record.order_line = False
            if record.package_ids:
                product_list = record.package_ids.parse_multi_package()
                for product in product_list:
                    product_id = ProductObj.browse(int(product[0]))
                    record.order_line += record.order_line.new({
                        'name': product_id.description or product_id.name,
                        'product_id': product_id.id,
                        'product_uom_qty': 1,
                        'price_unit': product[1],
                        'product_uom': product_id.uom_id.id or False,
                        'tax_id': product_id.taxes_id.ids or [],
                    })