# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    department_id = fields.Many2one('hr.department', 'Department', domain=[('type', 'in', ['pharmacies', 'center'])], track_visibility='onchange')

    @api.model
    def find_stock_location_employee(self):
        PickingType = self.env['stock.picking.type'].sudo()
        warehouse = self.find_stock_warehouse_employee()
        if warehouse:
            picking_type = PickingType.search([('warehouse_id', '=', warehouse.id), ('code', '=', 'outgoing')])
            location = picking_type.default_location_src_id
            if location:
                return location
        return False

    @api.model
    def find_stock_warehouse_employee(self):
        WareHouse = self.env['stock.warehouse'].sudo()
        center = self.env['hr.department']._get_center_id(self._uid)
        warehouse = WareHouse.search([('department_id', '=', center.id)])
        if warehouse:
            return warehouse
        return False