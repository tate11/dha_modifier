# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AssetAsset(models.Model):
    _inherit = 'asset.asset'


    type = fields.Selection([
        ('nor', 'Normal Devices'),
        ('it', 'IT Devices')
    ], default='nor', string='Type', track_visibility='onchange')
    ip_address = fields.Char('IP Address', track_visibility='onchange')
    access_credential_ids = fields.One2many('equip.access.credential', 'asset_id', 'Access Credentials')
    net_info_ids = fields.One2many('asset.net.info', 'parent_id', 'Net Info')

class EquipmentCredential(models.Model):
    _name = 'equip.access.credential'

    name = fields.Char('Name')
    user = fields.Char('User', required=1)
    pwd = fields.Char('Password', required=1)
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Owner')
    asset_id = fields.Many2one('asset.asset', string='Asset ID', required=1, ondelete='cascade')
    
class EquipmentNetInfo(models.Model):
    _name = 'asset.net.info'

    name = fields.Char('Name', required=1)
    value = fields.Char('value', required=1)
    parent_id = fields.Many2one('asset.asset', 'Parent ID', required=1, ondelete='cascade')