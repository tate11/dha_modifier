# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class ConsumableSupplies(models.Model):
    _name = 'medic.consumable.supplies'
    _order = 'id desc'


    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product ID', required=1)
    qty = fields.Float('Quantity', default=1.0)
    product_uom_id = fields.Many2one('product.uom', string='Product Unit of Measure')

    medic_test_id = fields.Many2one('medic.test', string='Medic Test', ondelete='cascade')
    medic_img_id = fields.Many2one('base.image.test', string='Medic Img', ondelete='cascade')
    # medic_xq_img_id = fields.Many2one('xq.image.test', string='Medic XQ Img', ondelete='cascade')
    # medic_sa_img_id = fields.Many2one('sa.image.test', string='Medic SA Img', ondelete='cascade')
    # medic_dtd_img_id = fields.Many2one('dtd.image.test', string='Medic DTD Img', ondelete='cascade')

    product_template_id = fields.Many2one('product.template', 'Product Template Id', ondelete='cascade')
    medical_id = fields.Many2one('medic.medical.bill', 'Medic Medical Id', ondelete='cascade')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

    @api.multi
    def _get_product_qty_data(self, products):
        Product = self.env['product.product']
        res = {}
        result = []
        uom_id = {}
        for product in products:
            for line in product.consumable_supplies:
                if str(line.product_id.id) in res:
                    res[str(line.product_id.id)] += line.qty
                else:
                    res[str(line.product_id.id)] = line.qty
                uom_id[str(line.product_id.id)] = line.product_uom_id.id

        for record in res.items():
            result.append({
                'product_id': int(record[0]),
                'qty': record[1],
                'product_uom_id': uom_id[record[0]],
            })
        return result

    @api.model
    def _apply_stock_(self, center):
        PickingType = self.env['stock.picking.type'].sudo()
        Quant = self.env['stock.quant'].sudo()
        WareHouse = self.env['stock.warehouse'].sudo()
        if center:
            warehouse = WareHouse.search([('department_id', '=', center.id)])
            if warehouse:
                picking_type = PickingType.search([('warehouse_id', '=', warehouse.id), ('code', '=', 'outgoing')])
                location = picking_type.default_location_src_id
                if location:
                    for record in self:
                        quant_id = Quant.search(
                            [('product_id', '=', record.product_id.id), ('location_id', '=', location.id),
                             ('company_id', '=', self.env.user.company_id.id)], limit=1)
                        if quant_id:
                            quant_id.write({'qty': (quant_id.qty - record.qty)})
                        else:
                            Quant.create({
                                'product_id' : record.product_id.id,
                                'company_id' : self.env.user.company_id.id,
                                'location_id' : location.id,
                                'qty' : -(record.qty),
                            })
    
