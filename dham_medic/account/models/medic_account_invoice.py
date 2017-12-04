# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from datetime import date
from odoo.tools import amount_to_text_en
from ...service.vi_amount_to_text import  amount_to_text_vi
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT




class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

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
    
    
    
    @api.depends('partner_id')
    def _compute_insurrance(self):
        for record in self:
            if record.partner_id:
                record.insurrance_ids = record.partner_id.insurrance_ids
                
    @api.depends('amount_total')
    def _compute_amount_text(self):
        for record in self:
            record.vi_amount_text = amount_to_text_vi(record.amount_total, currency='')
        
        
    vi_amount_text = fields.Char('Vi Text Amount', compute='_compute_amount_text')
    customer_id = fields.Char(string='Customer ID', related='partner_id.customer_id', readonly=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='partner_id.sex', readonly=1)

    day_of_birth = fields.Date(string='Day of Birth', related='partner_id.day_of_birth', readonly=1)
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=1)
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
    medicine_order_id = fields.Many2one('medicine.order', 'Medicine Order')
    medical_bill_id = fields.Many2one('medic.medical.bill', 'Medical Order')
    company_check_id = fields.Many2one('res.partner.company.check', 'Company Check Source ID', copy=False)
    # contract_adding_services = fields.Many2one('res.partner.company.check', 'Adding Service', copy=False)
    order_type = fields.Selection([('none', 'None'), ('medical', 'Medical'), ('medicine', 'Medicine')],
                                  string='Order Type', default='none', track_visibility='onchange')
    package_ids = fields.Many2many('medic.package', 'medic_account_invoice_package_ref', 'invoice_id', 'package_id',
                                   'Packages', domain=[('type', '=', 'person')])
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
        help='Pricelist for current invoice.'
    )

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.type in ['out_invoice', 'out_refund'] and not self.env.context.get('default_pricelist_id',False):
            self.pricelist_id = None
            if self.partner_id:
                self.pricelist_id = self.partner_id.property_product_pricelist
        return res


    @api.model
    def _get_account_id(self):
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            return AccountInvoiceLine.with_context(
                journal_id=default_journal.id)._default_account() or False
        return False

    @api.onchange('partner_id')
    def onchange_contract_partner_id_(self):
        if self.env.context.get('default_contract_adding_services', False):
            Contract = self.env['res.partner.company.check'].sudo().search(
                [('id', '=', self.env.context.get('default_contract_adding_services'))])
            self.medical_bill_id
            if self.partner_id and Contract:
                self.medical_bill_id = self.env['medic.medical.bill'].search([('company_check_id', '=', Contract.id),('customer','=', self.partner_id.id)]).id or False
            if Contract:
                return {
                    'domain' : {
                        'partner_id': [('id', 'in', Contract.employees.ids)]
                    }
                }

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
                        'name': product_id.description or product_id.name,
                        'product_id': product_id.id,
                        'account_id': default_account_id,
                        'quantity': 1,
                        'price_unit': product[1],
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
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for record in self.filtered(lambda r: r.state == 'open' and r.order_type == 'medical'):
            record._routing_invoice_line_()
        return res

    @api.model
    def _routing_invoice_line_(self):
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        Department = self.env['hr.department']

        company_check_id = False
        new_bill = False
        product_ids = False
        medical_bill_pro = self.invoice_line_ids.filtered(
            lambda r: r.product_id.type == 'service' and r.product_id.create_medical_bill == True)
        if medical_bill_pro:
            product_ids = medical_bill_pro.mapped('product_id.id')

        if self.medical_bill_id:
            company_check_id = self.medical_bill_id.company_check_id.id
            MedicalBill += self.medical_bill_id.related_medical_bill_ids

        # combine các related medical          
        if product_ids and len(product_ids) > 0 and not self.medical_bill_id:
            new_bill = MedicalBill.create({
                'customer': self.partner_id.id,
                'invoice_id': self.id,
                'service_ids': [(6, 0, product_ids)],
                'center_id': self.center_id.id or False,
                'building_id': False,
                'reason': self.reason,
                'prognostic': self.prognostic,
                'company_check_id': company_check_id,
            })
            MedicalBill += new_bill

            # SAVE RELATED
            MedicalBill.write({
                'related_medical_bill_ids': [(6, 0, MedicalBill.ids or [])]
            })
        elif product_ids and len(product_ids) > 0 and self.medical_bill_id:
            self.medical_bill_id.write({'service_ids': [(4, x) for x in product_ids], 'adding_service_ids': [(4, x) for x in product_ids]})

        for line in self.invoice_line_ids:
            if line.product_id and line.product_id.type == 'service':
                if line.product_id.service_type:
                    is_adding = True if self.medical_bill_id else False
                    MedicTest.create({
                        'type': line.product_id.service_type.id,
                        'center_id': self.center_id.id,
                        'product_test': line.product_id.id,
                        'customer': self.partner_id.id,
                        'doctor_assign': self.doctor_assign.id or False,
                        'related_medical_bill': [(6, 0, MedicalBill.ids)],
                        'company_check_id': company_check_id,
                        'is_adding' : is_adding,
                    })


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    order_type = fields.Selection([('none', 'None'), ('medical', 'Medical'), ('medicine', 'Medicine')],
                                  string='Order Type', default='none')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()

        if self.invoice_id.type not in ['out_invoice', 'out_refund']:
            return res

        partner = self.invoice_id.partner_id
        pricelist = self.invoice_id.pricelist_id
        product = self.product_id

        if not partner or not product or not pricelist:
            return res

        inv_date = self.invoice_id.date_invoice or date.today().strftime(DT)
        product = product.with_context(
            lang=partner.lang,
            partner=partner.id,
            quantity=self.quantity,
            date=inv_date,
            pricelist=pricelist.id,
            uom=self.uom_id.id
        )

        self.price_unit = self.env['account.tax']._fix_tax_included_price(
            product.price,
            product.taxes_id,
            self.invoice_line_tax_ids
        )
        return res
    
    @api.onchange('order_type')
    def onchange_order_type(self):
        if self.order_type == 'medical':
            return {
                'domain': {
                    'product_id': [('type', '=', 'service')]
                }
            }
    


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.model
    def get_default_journal_id(self):
        return self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id or False

    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))], default=get_default_journal_id)
