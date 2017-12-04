# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MedicPackage(models.Model):
    _name = 'medic.package'
    _order = 'id desc'

    @api.depends('line_ids.price')
    def _amount_all(self):
        for record in self:
            record.total_price = sum(line.price for line in record.line_ids)
            record.total_price_male = sum(
                line.price for line in record.line_ids.filtered(lambda r: r.product_id.sex in ['male', False]))
            record.total_price_female = sum(
                line.price for line in record.line_ids.filtered(lambda r: r.product_id.sex in ['female', False]))

    name = fields.Char('Name')
    type = fields.Selection([('person', 'Person'), ('company', 'Company')], 'Package Type', default='person')
    total_price = fields.Float(string='Amount', compute='_amount_all', track_visibility='onchange')
    total_price_male = fields.Float(string='Amount / Male', compute='_amount_all',
                                    track_visibility='onchange')
    total_price_female = fields.Float(string='Amount / Female', compute='_amount_all',
                                      track_visibility='onchange')

    line_ids = fields.One2many('medic.package.line', 'parent_id', 'Service Lines', required=1)

    # Combine nhieu package lai thanh 1 list gom product va gia
    # param dict or list
    @api.model
    def parse_multi_package(self, return_type='list'):
        product_dict = {}
        res = []
        for record in self:
            for line in record.line_ids:
                if str(line.product_id.id) not in product_dict:
                    product_dict[str(line.product_id.id)] = line.price
                else:
                    if line.price > product_dict[str(line.product_id.id)]:
                        product_dict[str(line.product_id.id)] = line.price
        for product in product_dict.items():
            res.append((int(product[0]), product[1]))
        if return_type == 'dict':
            return product_dict
        return res


class MedicPackageLine(models.Model):
    _name = 'medic.package.line'

    parent_id = fields.Many2one('medic.package', 'Parent ID', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=1, domain=[('type', '=', 'service')])
    price = fields.Float('Unit Price', required=1)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price
