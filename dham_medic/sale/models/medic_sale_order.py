# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id')
    def _compute_check_partner_(self):
        for record in self:
            if record.partner_id.is_company:
                record.check_partner_company = True

    receive_ids = fields.One2many('dham.patient.recieve', 'sale_order_id', 'Receive ID')
    order_type = fields.Selection([('medicine', 'Medicine'), ('food-drink', 'Foods and Drinks'), ('none', 'None')],
                                  default='none', string='Order Type')
    medic_contract_id = fields.Many2one('res.partner.company.check', 'Medic Contract')
    check_partner_company = fields.Boolean('Check Partner',compute='_compute_check_partner_')
    package_ids = fields.Many2many('medic.package', 'medic_sale_order_package_package_ref', 'order_id',
                                   'package_id', 'Packages', domain=[('type', '=', 'company')], required=1)

    @api.onchange('package_ids')
    def onchange_package_ids(self):
        if 'no_onchange_package' in self.env.context:
            return
        ProductObj = self.env['product.product']

        for record in self:
            record.invoice_line_ids = False
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

    @api.onchange('order_type')
    def onchange_order_type(self):
        warehouse = self.env['hr.department'].sudo().find_ware_house(self._uid)
        if self.order_type == 'medicine':
            if warehouse:
                self.warehouse_id = warehouse.id
                self.picking_policy = 'one'

        if self.order_type == 'food-drink':
            if warehouse:
                self.warehouse_id = warehouse.id
                self.picking_policy = 'one'
    
    @api.multi
    def action_create_package(self):
        for record in self:
            record._action_create_package()
        return 
    
    @api.model
    def _action_create_package(self):
        MedicContract = self.env['res.partner.company.check']
        if self.order_line:
            package_id = self.parse_medic_package()
            data = {
                'name' : self.partner_id.name + ' - ' + self.name,
                'company_id' :  self.partner_id.id,
                'package_ids': [(6, 0,[package_id.id])],
                'sale_order_id' : self.id,
            }
            new_contract = MedicContract.create(data)
            self.write({'medic_contract_id' : new_contract.id})
            return new_contract
        
    @api.model
    def parse_medic_package(self):
        Package = self.env['medic.package']
        data = {
            'name' : self.partner_id.name + ' - ' + self.name,
            'type' : 'company',
            'line_ids' : [],
        }
        for line in self.order_line:
            data['line_ids'].append(
                (0, 0, {
                    'product_id' : line.product_id.id,
                    'price' : line.price_unit,
                })
            )
        return Package.create(data)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_type = fields.Selection([('medicine', 'Medicine'), ('food-drink', 'Foods and Drinks'), ('none', 'None')],
                                  default='none', string='Order Type')

    @api.onchange('order_type')
    def onchange_order_type(self):
        if self.order_type == 'medicine':
            try:
                return {
                    'domain': {
                        'product_id': [('categ_id', '=', self.env.ref('dham_medic.product_ctg_medicines').id)]
                    }
                }
            except:
                pass
        if self.order_type == 'food-drink':
            try:
                return {
                    'domain': {
                        'product_id': [('categ_id', '=', self.env.ref('dham_medic.product_ctg_food_drink').id)]
                    }
                }
            except:
                pass