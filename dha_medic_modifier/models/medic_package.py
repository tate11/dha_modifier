# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicPackage(models.Model):
    _name = 'medic.package'

    name = fields.Char('Name')
    type = fields.Selection([('person','Person'),('company','Company')], 'Package Type', default='person')
    total_price = fields.Float('Price')
    line_ids = fields.One2many('medic.package.line','parent_id', 'Service Lines', required=1)

    @api.model
    def parse_multi_package(self):
        product_dict = {}
        res = []
        for record in self:
            for line in record.line_ids:
                if str(line.product_id.id) not in product_dict:
                    product_dict[str(line.product_id.id)] = line.qty
                else:
                    if line.qty > product_dict[str(line.product_id.id)]:
                        product_dict[str(line.product_id.id)] = line.qty
        product_dict = product_dict.items()
        for product in product_dict:
            res.append((int(product[0]), product[1]))
        return res

class MedicPackageLine(models.Model):
    _name = 'medic.package.line'

    parent_id = fields.Many2one('medic.package', 'Parent ID', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    qty = fields.Float('Quantity', default=1.0)