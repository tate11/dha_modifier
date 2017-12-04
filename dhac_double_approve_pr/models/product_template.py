# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def _get_domain_respond_id(self):
        res_ids = self.env.ref('purchase.group_purchase_user').users.ids
        return [('id', 'in', res_ids)]

    purchase_respond_id = fields.Many2one('res.users', 'Purchase Respond', domain=_get_domain_respond_id) 