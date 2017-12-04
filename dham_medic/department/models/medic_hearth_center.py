# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class hr_department(models.Model):
    _inherit = 'hr.department'

    type = fields.Selection([('center', 'Center'), ('buildings', 'Buildings'), ('pharmacies', 'Pharmacies'),('room','Room')],
                            string='Type', track_visibility='onchange')

    buildings_type = fields.Many2one('hr.department.building.type', 'Buildings Type', track_visibility='onchange')
    code = fields.Char('Code', size=3, track_visibility='onchange')
    address = fields.Char('Address', track_visibility='onchange')
    mobile = fields.Char('Mobile', track_visibility='onchange')
    email = fields.Char('Email', track_visibility='onchange')

    @api.onchange('type')
    def onchange_type(self):
        if self.type  in ['buildings', 'pharmacies']:
            return {
                'domain' : {
                    'parent_id' : [('type', '=', 'center')]
                }
            }
        if self.type  in ['room']:
            return {
                'domain' : {
                    'parent_id' : [('type', '=', 'buildings')]
                }
            }

    @api.model
    def find_center(self):
        def _find_center(center):
            if center.type == 'center':
                return center
            elif center.type != 'center' and not center.parent_id:
                return False
            else:
                return _find_center(center.parent_id)
        if self.type == 'center':
            return self
        else:
            return _find_center(self)

    @api.model
    def find_building(self):
        def _find_building(building):
            if building.type == 'buildings':
                return building
            elif building.type != 'buildings' and not building.parent_id:
                return False
            else:
                return _find_building(building.parent_id)

        if self.type == 'buildings':
            return self
        else:
            return _find_building(self)

    @api.model
    def _get_center_id(self, user_id):
        employee_id = self.env['hr.employee'].search([('user_id', '=', user_id)])
        if employee_id:
            if employee_id[0].department_id:
                return employee_id[0].department_id.find_center()
        return False
    
    @api.model
    def find_ware_house(self, user_id):
        WareHouse = self.env['stock.warehouse']
        employee_id = self.env['hr.employee'].search([('user_id', '=', user_id)])
        if employee_id:
            center = False
            pharmacies = False
            if not employee_id[0].department_id.parent_id and employee_id[0].department_id.type=='pharmacies':
                pharmacies = employee_id[0].department_id

            elif employee_id[0].department_id:
                center = employee_id[0].department_id.find_center()

            if center:
                return WareHouse.search([('department_id','=',center.id)])
            if pharmacies:
                return WareHouse.search([('department_id','=',pharmacies.id)])
        return False

            
class hr_department_building_type(models.Model):
    _name = 'hr.department.building.type'

    name = fields.Char('Name', required=1, translate=True)
