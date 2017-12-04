# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero
import base64


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    quantity = fields.Float('Quantity')
    asset_asset_ids = fields.Many2many('asset.asset', 'accout_asset_asset_asset_asset_rel','id1','id2', string='Assets')
    request_by = fields.Many2one('res.users', 'Request By')

    @api.model
    def create(self, vals):
        Asset = self.env['asset.asset']
        if vals.get('quantity', False):
            vendor = False
            request_by = False
            if vals.get('invoice_id', False):
                vendor = self.env['account.invoice'].sudo().browse(vals.get('invoice_id')).partner_id.id
            for i in range(0, int(vals.get('quantity'))):
                Asset += Asset.sudo().create({
                    'name': vals['name'] or '',
                    'vendor_id': vendor,
                    'purchase_date': datetime.now().strftime(DF),
                    'user_id': vals.get('request_by', False),
                })
            vals['asset_asset_ids'] = [(6, 0, Asset.ids)]
        res = super(AccountAssetAsset, self).create(vals)
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    def asset_create(self):

        try:
            request_by = self.purchase_line_id.purchase_request_lines.filtered(lambda r: r.requested_by != False)[0].requested_by.id
        except:
            request_by = False
        if self.asset_category_id:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal_signed,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.company_currency_id.id,
                'date': self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
                'quantity' :  self.quantity,
                'request_by': request_by,
            }
            changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
            vals.update(changed_vals['value'])
            asset = self.env['account.asset.asset'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True

class asset_asset(models.Model):
    _inherit = 'asset.asset'


    @api.model
    def create(self, vals):
        if not vals['asset_number']:
            vals['asset_number'] = self.env['ir.sequence'].next_by_code('asset.asset.seq')
        res = super(asset_asset, self).create(vals)
        return res

    @api.depends('asset_number')
    def _compute_qr_code(self):
        for record in self:
            record.barcode_image = record.action_generate_barcode(record.asset_number)
        

    @api.model
    def action_generate_barcode(self, data):
        Report = self.env['report']
        if data:
            data_image = base64.b64encode(Report.barcode('QR', data, width=100, height=100))
            return data_image
        return False
    
    @api.depends('name', 'serial')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            serial = (' ( ' + record.serial + ' )') if record.serial else ''
            record.display_name = name + serial

    barcode_image = fields.Binary('QR Code', compute='_compute_qr_code')
    display_name = fields.Char('Display Name', compute='_compute_display_name')