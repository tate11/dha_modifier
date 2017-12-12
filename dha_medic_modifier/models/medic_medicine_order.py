# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicineOrder(models.Model):
    _name = 'medicine.order'
    _inherit = 'mail.thread'
    _order = 'id desc'


    name = fields.Char('Number', readonly=1)
    medical_id = fields.Many2one('medic.medical.bill', 'Medical Bill')
    state = fields.Selection([('new', 'New'), ('validate', 'Validated')], 'Status', default='new', track_visibility='onchange')

    patient = fields.Many2one('dham.patient', 'Patient', track_visibility='onchange', index=1)
    customer = fields.Many2one('res.partner', 'Customer', track_visibility='onchange')
    customer_id = fields.Char(string='Customer ID', related='patient.patient_id', readonly=1)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex', related='patient.sex', readonly=1)
    day_of_birth = fields.Date(string='Day of Birth', related='patient.day_of_birth', readonly=1)

    line_ids = fields.One2many('medicine.order.line', 'parent_id', 'Medicine Order Line')

    doctor_assign = fields.Many2one('hr.employee', 'Assigned By', readonly=1, track_visibility='onchange')
    assign_date = fields.Datetime('Assigned Date', default=lambda *a: datetime.datetime.now(), readonly=1, track_visibility='onchange')

    center_id = fields.Many2one('hr.department', 'Center', related='medical_id.center_id', readonly=1, store=True, track_visibility='onchange')
    building_id = fields.Many2one('hr.department', 'Building', related='medical_id.building_id', readonly=1, store=True, track_visibility='onchange')
    room_id = fields.Many2one('hr.department', 'Room', related='medical_id.room_id', readonly=1, store=True, track_visibility='onchange')
    check_created = fields.Boolean('Check Created', default=False)

    medicine_package = fields.Many2many('medicine.order.package', 'medicine_order_medicine_order_package_rel',
                                        'medicine_order', 'package_id', 'Packages')

    @api.onchange('medicine_package')
    def onchange_medicine_package(self):
        self.line_ids = False
        lists = self.medicine_package.parse_multi_package()
        for data in lists:
            self.line_ids += self.line_ids.new({
                'product_id': data[0],
                'product_qty': data[1],
            })

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
        sale_data = self._prepare_sale_order_data(self.customer)
        sale_line_data = self._prepare_sale_order_line_data(self.line_ids)
        sale_data['order_line'] = sale_line_data
        new_order = self.env['sale.order'].create(sale_data)
        new_order.action_confirm()
        invoices = new_order.action_invoice_create()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['domain'] = [('id', 'in', invoices)]
        return action

    @api.model
    def _prepare_sale_order_data(self, partner):

        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = self.env['hr.department'].find_ware_house(self._uid)
        return {
            'warehouse_id': warehouse.id if warehouse else False,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'fiscal_position_id': partner.property_account_position_id.id,
            'partner_shipping_id': partner_addr['delivery'],
            'payment_term_id': self.env.ref('account.account_payment_term_immediate').id or False,
            'picking_policy': 'one',
        }

    @api.model
    def _prepare_sale_order_line_data(self, lines):
        res = []
        for line in lines:
            res.append((0, 0, {
                'name': line.product_id and line.product_id.name or line.name,
                'product_uom_qty': line.product_qty,
                'product_id': line.product_id and line.product_id.id or False,
                'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
                'price_unit': line.product_id.uom_id.id or False,
                'tax_id': line.product_id.taxes_id.ids or [],
            }))
        return res


class MedicineOrderLine(models.Model):
    _name = 'medicine.order.line'

    @api.model
    def _get_medicine_product_domain(self):
        try:
            return [('categ_id', '=', self.env.ref('dha_medic_modifier.product_ctg_medicines').id)]
        except:
            return []

    product_id = fields.Many2one('product.product', 'Product', domain=_get_medicine_product_domain, required=1)
    description = fields.Many2one('medicine.description', 'Description', required=1)
    qty_dose = fields.Float('Quantity per Dose', default=1)
    dose = fields.Integer('Dose Number', default=1)
    appoint_qty = fields.Float('Quantity', default=1)
    product_qty = fields.Float('Real Quantity', default=1)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    parent_id = fields.Many2one('medicine.order', 'Medicine Order')
    check_created = fields.Boolean('Check Created', default=False)

    @api.onchange('qty_dose', 'dose')
    def onchange_dose_qty(self):
        self.appoint_qty = self.dose * self.qty_dose

    @api.onchange('appoint_qty','product_id')
    def onchange_appoint_qty(self):
        if self.product_id:
            self.product_qty = self.appoint_qty
            self.product_uom = self.product_id.uom_id

            # kiem tra so luong thuoc con lai
            Quant = self.env['stock.quant'].sudo()
            WareHouse = self.env['stock.warehouse'].sudo()
            location = WareHouse.find_stock_location_employee()
            if location:
                quant_ids = Quant.search(
                    [('product_id', '=', self.product_id.id), ('location_id', '=', location.id),
                     ('company_id', '=', self.env.user.company_id.id)])
                stock_qty = 0
                if quant_ids:
                    stock_qty = sum(x.qty for x in quant_ids)
                if stock_qty < self.appoint_qty:
                    return {
                        'warning': {
                            'title': _('Warning!'),
                            'message': _('You plan to sell %s %s but you only have %s %s available!') % (
                            self.appoint_qty, self.product_uom.name, stock_qty, self.product_uom.name),
                        }
                    }

    @api.model
    def create(self, vals):
        vals['check_created'] = True
        res = super(MedicineOrderLine, self).create(vals)
        return res


class MedicineDescription(models.Model):
    _name = 'medicine.description'

    name = fields.Char('Name', required=1)


class MedicineOrderPackage(models.Model):
    _name = 'medicine.order.package'

    name = fields.Char('Name', required=1)
    line_ids = fields.One2many('medicine.order.package.line', 'parent_id', 'Lines', required=1)

    @api.model
    def parse_multi_package(self):
        product_dict = {}
        res = []
        for record in self:
            for line in record.line_ids:
                if str(line.product_id.id) not in product_dict:
                    product_dict[str(line.product_id.id)] = line.quantity
                else:
                    if line.quantity > product_dict[str(line.product_id.id)]:
                        product_dict[str(line.product_id.id)] = line.quantity
        product_dict = product_dict.items()
        for product in product_dict:
            res.append((int(product[0]), product[1]))
        return res


class MedicineOrderPackageLine(models.Model):
    _name = 'medicine.order.package.line'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    quantity = fields.Float('Quantity', default=1)
    parent_id = fields.Many2one('medicine.order.package', 'Parent Id', ondelete='cascade', required=1)
