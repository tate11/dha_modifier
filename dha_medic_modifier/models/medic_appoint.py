# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicAppoint(models.Model):
    _name = 'medic.appoint'

    @api.model
    def get_default_doctor(self):
        Employee = self.env['hr.employee']
        return Employee.search([('user_id','=',self._uid)], limit=1).id or False


    name = fields.Char('Number', readonly=1, default='/')
    state = fields.Selection([('new', 'New'), ('validate', 'Validated')], 'Status', default='new')
    customer = fields.Many2one('res.partner', 'Customer')
    customer_id = fields.Char(string='Customer ID', related='customer.customer_id', readonly=1)
    sex_id = fields.Many2one('res.partner.sex', string='Sex', related='customer.sex_id', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='customer.day_of_birth', readonly=1)

    doctor_assign = fields.Many2one('hr.employee', 'Doctor Appoint', readonly=1)
    assign_date = fields.Datetime('Appoint Date', default=lambda *a: datetime.datetime.now())

    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    line_ids = fields.One2many('medic.appoint.line', 'parent_id', 'Lines')

    package_ids = fields.Many2many('medic.package', 'medic_appoint_package_ref', 'appoint_id', 'package_id', 'Packages', domain=[('type', '=', 'person')])

    @api.onchange('package_ids')
    def onchange_package_ids(self):
        for record in self:
            record.line_ids = False
            product_list = record.package_ids.parse_multi_package()
            for product in product_list:
                record.line_ids += record.line_ids.new({
                    'product_id': product[0],
                    'qty': product[1],
                })

    @api.multi
    def action_validate(self):
        self.write({'state': 'validate'})
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        default_account_id = False
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            default_account_id = AccountInvoiceLine.with_context(journal_id=default_journal.id)._default_account() or False
        invoice_line_ids = []
        for line in self.line_ids:
            invoice_line_ids.append({
                'product_id': line.product_id.id,
                'uom_id': line.product_id.uom_id.id or False,
                'price_unit': line.product_id.lst_price,
                'invoice_line_tax_ids': line.product_id.taxes_id.ids or [],
                'name': line.product_id.description or line.product_id.name,
                'quantity': line.qty,
                'account_id': default_account_id,
            })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': False,
            'context': {'default_partner_id': self.customer.id, 'default_medical_bill_id': self.medical_bill_id .id,
                        'default_invoice_line_ids': invoice_line_ids, 'form_view_ref': 'account.invoice_form'
                , 'default_order_type': 'medical', 'default_center_id' : self.medical_bill_id.center_id.id or False,'no_onchange_package' : True}
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medic.appoint.seq')
        Employee = self.env['hr.employee']
        vals['doctor_assign'] = Employee.search([('user_id', '=', self._uid)], limit=1).id or False
        return super(MedicAppoint, self).create(vals)

class MedicAppointLine(models.Model):
    _name = 'medic.appoint.line'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    qty = fields.Float('Quantity', default=1.0)
    parent_id = fields.Many2one('medic.appoint', 'Appoint')
