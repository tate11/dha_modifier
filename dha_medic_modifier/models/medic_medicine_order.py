# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicineOrder(models.Model):
    _name = 'medicine.order'

    name = fields.Char('Number', readonly=1)
    medical_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    state = fields.Selection([('new', 'New'), ('validate', 'Validated')], 'Status', default='new')
    customer = fields.Many2one('res.partner', 'Customer')
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex_id = fields.Many2one('res.partner.sex', string='Sex', related='customer.sex_id', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)

    line_ids = fields.One2many('medicine.order.line', 'parent_id', 'Medicine Order Line')

    doctor_assign = fields.Many2one('hr.employee', 'Doctor Assigned', readonly=1)
    assign_date = fields.Datetime('Assigned Date', default=lambda *a: datetime.datetime.now())

    center_id = fields.Many2one('hr.department', 'Center', related='medical_id.center_id', readonly=1, store=True)
    building_id = fields.Many2one('hr.department', 'Building', related='medical_id.building_id', readonly=1, store=True)
    room_id = fields.Many2one('hr.department', 'Room', related='medical_id.room_id', readonly=1, store=True)
    check_created = fields.Boolean('Check Created', default=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medicine.order.code')
        Employee = self.env['hr.employee']
        vals['doctor_assign'] = Employee.search([('user_id', '=', self._uid)], limit=1).id or False
        vals['check_created'] = True
        return super(MedicineOrder, self).create(vals)

    @api.multi
    def action_validate(self):
        self.write({'state': 'validate'})
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        default_account_id = False
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            default_account_id = AccountInvoiceLine.with_context(journal_id = default_journal.id)._default_account() or False
        invoice_line_ids = []
        for line in self.line_ids:
            invoice_line_ids.append({
                'product_id': line.product_id.id,
                'uom_id' : line.product_id.uom_id.id or False,
                'price_unit' : line.product_id.lst_price,
                'invoice_line_tax_ids' : line.product_id.taxes_id.ids or [],
                'name': line.description.name or '',
                'quantity': line.product_qty,
                'account_id' : default_account_id,
            })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': False,
            'context': {'default_partner_id': self.customer.id, 'default_medicine_order_id': self.id,
                        'default_invoice_line_ids': invoice_line_ids, 'form_view_ref': 'account.invoice_form'
                , 'default_order_type': 'medicine', 'no_onchange_package' : True}
        }


class MedicineOrderLine(models.Model):
    _name = 'medicine.order.line'

    product_id = fields.Many2one('product.product', 'Product')
    description = fields.Many2one('medicine.description', 'Description', required=1)
    qty_dose = fields.Float('Quantity per Dose', default=1)
    dose = fields.Integer('Dose Number', default=1)
    product_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    parent_id = fields.Many2one('medicine.order', 'Medicine Order')

    @api.onchange('qty_dose', 'dose')
    def onchange_dose_qty(self):
        self.product_qty = self.dose * self.qty_dose

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.id if self.product_id else False

class MedicineDescription(models.Model):
    _name = 'medicine.description'

    name = fields.Char('Name', required=1)