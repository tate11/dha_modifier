# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import odoo.addons.decimal_precision as dp

class DHAMReceive(models.Model):
    _name = 'dham.patient.recieve'
    _order = 'id desc'
    _inherit = 'mail.thread'

    @api.depends('line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.parent_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.patient.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

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

    @api.multi
    def button_dummy(self):
        return True

    @api.depends('patient')
    def _compute_insurrance(self):
        for record in self:
            if record.patient:
                record.insurrance_ids = record.patient.insurrance_ids

    name = fields.Char('Receive Number')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancel','Canceled')
    ], readonly=1, index=1, string='Status', default='draft')

    user_id = fields.Many2one('res.users', 'Responsible', default= lambda self: self.env.user.id or False)
    date = fields.Datetime('Create Time', default=lambda self: fields.Datetime.now(), readonly=1)

    patient = fields.Many2one('dham.patient', 'Patient', required=1)
    partner_id = fields.Many2one('res.partner', 'Partner ID', related='patient.partner_id', store=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='patient.sex', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='patient.day_of_birth', readonly=1)
    insurrance_ids = fields.Many2many('dham.patient.insurrance', compute='_compute_insurrance', string='Insurrance',
                                      readonly=1)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get())
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')

    line_ids = fields.One2many('dham.patient.recieve.line', 'parent_id', string='Services',required=1)
    note = fields.Text('Note')
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
    sale_order_id = fields.Many2one('sale.order','Sale Order Id')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('patient.receive.seq')
        res = super(DHAMReceive, self).create(vals)
        return res

    @api.multi
    @api.onchange('patient')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        values = {
            'pricelist_id': self.patient.partner_id.property_product_pricelist and self.patient.partner_id.property_product_pricelist.id or False,
        }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.patient.lang).env.user.company_id.sale_note
        self.update(values)

    @api.onchange('patient')
    def _onchange_patient(self):
        self.partner_id = self.patient and self.patient.partner_id.id or False
        if self.env.context.get('default_contract_adding_services', False):
            Contract = self.env['res.partner.company.check'].sudo().search(
                [('id', '=', self.env.context.get('default_contract_adding_services'))])
            if self.patient and Contract:
                self.medical_bill_id = self.env['medic.medical.bill'].search(
                    [('company_check_id', '=', Contract.id), ('customer', '=', self.patient.id)]).id or False
            if Contract:
                return {
                    'domain': {
                        'patient': [('id', 'in', Contract.employees.ids)]
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
            record.line_ids = False
            if record.package_ids:
                product_list = record.package_ids.parse_multi_package()
                for product in product_list:
                    product_id = ProductObj.browse(int(product[0]))
                    record.line_ids += record.line_ids.new({
                        'name': product_id.description or product_id.name,
                        'product_id': product_id.id,
                        'product_uom_qty': 1,
                        'price_unit': product[1],
                        'product_uom': product_id.uom_id.id or False,
                        'tax_id': product_id.taxes_id.ids or [],
                    })

    @api.multi
    def action_paid(self):
        self.write({'state': 'paid'})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def action_confirm(self):
        for record in self:
            record.sudo().routing_receive()
            order = record.sudo().create_sale_order()
            order.sudo().action_confirm()
            order.sudo().action_invoice_create()
            record.write({'state': 'confirmed','sale_order_id': order.id})
        return True

    @api.model
    def routing_receive(self):
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        Department = self.env['hr.department']

        company_check_id = False
        new_bill = False
        product_ids = False
        medical_bill_pro = self.line_ids.filtered(
            lambda r: r.product_id.type == 'service' and r.product_id.create_medical_bill == True)
        if medical_bill_pro:
            product_ids = medical_bill_pro.mapped('product_id.id')

        if self.medical_bill_id:
            company_check_id = self.medical_bill_id.company_check_id.id
            MedicalBill += self.medical_bill_id.related_medical_bill_ids

        # combine các related medical
        if product_ids and len(product_ids) > 0 and not self.medical_bill_id:
            new_bill = MedicalBill.create({
                'patient': self.patient.id,
                'receive_id': self.id,
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
            self.medical_bill_id.write(
                {'service_ids': [(4, x) for x in product_ids], 'adding_service_ids': [(4, x) for x in product_ids]})

        for line in self.line_ids:
            if line.product_id and line.product_id.type == 'service':
                if line.product_id.service_type:
                    is_adding = True if self.medical_bill_id else False
                    self.env[line.product_id.service_type.model_name].create({
                        'type': line.product_id.service_type.id,
                        'center_id': self.center_id.id,
                        'product_test': line.product_id.id,
                        'patient': self.patient.id,
                        'doctor_assign': self.doctor_assign.id or False,
                        'related_medical_bill': [(6, 0, MedicalBill.ids)],
                        'company_check_id': company_check_id,
                        'is_adding': is_adding,
                    })
        return

    @api.model
    def create_sale_order(self):
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        order = SaleOrder.create({
            'partner_id': self.patient.partner_id.id,
            'partner_invoice_id': self.patient.partner_id.id,
            'partner_shipping_id': self.patient.partner_id.id,
            'date_order': datetime.today(),
            'pricelist_id': self.pricelist_id.id,
            'medic_receive_id' : self.id,
        })
        SaleOrder += order
        for line in self.line_ids:
            SaleOrderLine.create({
                'name': line.name,
                'order_id': order.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'tax_id' : [(6, 0, [line.tax_id.ids])],
                'price_unit' : line.price_unit,
                'sequence' :  line.sequence
            })
        return SaleOrder

class DHAMReceiveLine(models.Model):
    _name = 'dham.patient.recieve.line'
    _order = 'id, sequence, parent_id'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.parent_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.parent_id.patient.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    parent_id = fields.Many2one('dham.patient.recieve', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)


    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    price_reduce = fields.Monetary(compute='_get_price_reduce', string='Price Reduce', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    price_reduce_taxinc = fields.Monetary(compute='_get_price_reduce_tax', string='Price Reduce Tax inc', readonly=True,
                                          store=True)
    price_reduce_taxexcl = fields.Monetary(compute='_get_price_reduce_notax', string='Price Reduce Tax excl',
                                           readonly=True, store=True)

    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True),('type','=','service')],
                                 change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)


    salesman_id = fields.Many2one(related='parent_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='parent_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='parent_id.company_id', string='Company', store=True, readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
    ], related='parent_id.state', string='Parent Status', readonly=True, copy=False, store=True, default='draft')

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.parent_id.patient.partner_id.property_account_position_id or False
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.parent_id.patient.partner_id) if fpos else taxes

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sale order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.parent_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.parent_id.pricelist_id.id).price
        final_price, rule_id = self.parent_id.pricelist_id.get_product_price_rule(self.product_id,
                                                                                 self.product_uom_qty or 1.0,
                                                                                 self.parent_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.parent_id.partner_id.id, date=self.parent_id.date)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id,
                                                                                              self.product_uom_qty,
                                                                                              self.product_uom,
                                                                                              self.parent_id.pricelist_id.id)
        if currency_id != self.parent_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price,
                                                                                                            self.parent_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.parent_id.partner_id.lang,
            partner=self.parent_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.parent_id.date,
            pricelist=self.parent_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.parent_id.pricelist_id and self.parent_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.parent_id.pricelist_id and self.parent_id.partner_id:
            product = self.product_id.with_context(
                lang=self.parent_id.patient.lang,
                partner=self.parent_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.parent_id.date,
                pricelist=self.parent_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)
