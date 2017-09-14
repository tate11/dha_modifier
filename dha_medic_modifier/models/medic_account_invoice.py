# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _get_center_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if employee_id:
            if employee_id[0].department_id:
                return employee_id[0].department_id.find_center()
        return False

    @api.depends('partner_id')
    def _compute_insurrance(self):
        for record in self:
            if record.partner_id:
                record.insurrance_ids = record.partner_id.insurrance_ids

    customer_id = fields.Char(string='Customer ID', related='partner_id.customer_id', readonly=1)
    sex_id = fields.Many2one('res.partner.sex', string='Sex', related='partner_id.sex_id', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='partner_id.day_of_birth', readonly=1)
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=1)
    insurrance_ids = fields.Many2many('res.partner.insurrance', compute='_compute_insurrance', string='Insurrance', readonly=1)
    # ly do
    reason = fields.Text('Reason')
    # trieu chung
    prognostic = fields.Text('Prognostic')

    # PHong Kham

    center_id = fields.Many2one('hr.department', 'Center', default=_get_center_id, domain=[('type', '=', 'center')])
    building_id = fields.Many2one('hr.department', 'Building', domain=[('type', '=', 'buildings')])
    room_id = fields.Many2one('hr.department', 'Room', domain=[('type', '=', 'room')])
    doctor_assign = fields.Many2one('hr.employee', 'Assigned To')
    medicine_order_id = fields.Many2one('medicine.order', 'Medicine Order')
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Order')

    order_type = fields.Selection([('none', 'None'), ('medical', 'Medical'), ('medicine', 'Medicine')],
                                  string='Order Type', default='none')
    package_ids = fields.Many2many('medic.package', 'medic_account_invoice_package_ref', 'invoice_id', 'package_id', 'Packages', domain=[('type', '=', 'person')])

    @api.model
    def _get_account_id(self):
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            return AccountInvoiceLine.with_context(
                journal_id=default_journal.id)._default_account() or False
        return False

    @api.onchange('package_ids')
    def onchange_package_ids(self):
        if 'no_onchange_package' in self.env.context:
            return
        ProductObj = self.env['product.product']
        default_account_id = self._get_account_id()

        for record in self:
            record.invoice_line_ids = False
            if record.package_ids:
                product_list = record.package_ids.parse_multi_package()
                for product in product_list:
                    product_id = ProductObj.browse(int(product[0]))
                    record.invoice_line_ids += record.invoice_line_ids.new({
                        'name' : product_id.description or product_id.name,
                        'product_id': product_id.id,
                        'account_id': default_account_id,
                        'quantity': product[1],
                        'price_unit': product_id.lst_price,
                        'uom_id': product_id.uom_id.id or False,
                        'invoice_line_tax_ids': product_id.taxes_id.ids or [],
                    })

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

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        if 'state' in vals:
            if vals['state'] == 'paid':
                for record in self.filtered(lambda r: r.state == 'paid'):
                    record._routing_invoice_line_()
        return res

    @api.model
    def _routing_invoice_line_(self):
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        Department = self.env['hr.department']

        new_bill = False
        # combine các related medical
        medical_bill_pro = self.invoice_line_ids.filtered(
            lambda r: r.product_id.type == 'service' and r.product_id.create_medical_bill == True)
        while len(medical_bill_pro) > 0:
            same_type_line = medical_bill_pro.filtered(
                lambda r: r.product_id.buildings_type.id == medical_bill_pro[
                    0].product_id.buildings_type.id)

            building = False
            if self.center_id:
                building = Department.search([('type', '=', 'buildings'), ('parent_id', '=', self.center_id.id),
                                              ('buildings_type', '=', medical_bill_pro[0].product_id.buildings_type.id)],
                                             limit=1)

            product_ids = [x.product_id.id for x in same_type_line]
            new_bill = MedicalBill.create({
                'customer': self.partner_id.id,
                'invoice_id': self.id,
                'service_ids': [(6, 0, product_ids)],
                'center_id': self.center_id.id or False,
                'building_id': building.id or False,
                'reason': self.reason,
                'prognostic' : self.prognostic,
            })
            medical_bill_pro -= same_type_line
            MedicalBill += new_bill

        if self.medical_bill_id:
            MedicalBill += self.medical_bill_id.related_medical_bill_ids

        # SAVE RELATED
        MedicalBill.write({
            'related_medical_bill_ids': [(6, 0, MedicalBill.ids or [])]
        })

        for line in self.invoice_line_ids:
            if line.product_id and line.product_id.type == 'service':
                if line.product_id.service_type:
                    MedicTest.create({
                        'type': line.product_id.service_type.id,
                        'product_test': line.product_id.id,
                        'customer': self.partner_id.id,
                        'related_medical_bill': [(6, 0, MedicalBill.ids)],
                    })


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    order_type = fields.Selection([('none', 'None'), ('medical', 'Medical'), ('medicine', 'Medicine')],
                                  string='Order Type', default='none')
    @api.onchange('order_type')
    def onchange_order_type(self):
        if self.order_type == 'medical':
            return {
                'domain': {
                    'product_id':[('type','=','service')]
                }
            }

class account_payment(models.Model):
    _inherit = "account.payment"

    @api.model
    def get_default_journal_id(self):
        return self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id or False

    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))], default=get_default_journal_id)
