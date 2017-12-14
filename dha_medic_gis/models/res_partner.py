# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import openpyxl as px
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class ResPartnerType(models.Model):
    _name = 'res.partner.type'

    name = fields.Char('Name')
    code = fields.Char('Code')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_type(self):
        try:
            customer_type = self.env['res.partner.type'].search([('code', '=', 'customer')], limit=1)
            if customer_type:
                return customer_type
        except Exception, e:
            return

    lat = fields.Float('Latitude')
    lng = fields.Float('Longtitude')
    partner_type_id = fields.Many2one('res.partner.type', string='Type', default=_default_type)
    contact_address = fields.Char(compute='_compute_contact_address', string='Complete Address', store=True)

    @api.multi
    def write(self, values):
        res = super(ResPartner, self).write(values)
        for rec in self:
            if values.get('street', False) or values.get('street2', False) or values.get('ward', False) or values.get('district', False) or values.get('city_dropdown', False) or values.get('country_id', False):
                addr = rec._display_address(True)
                data = rec.get_lat_lng(addr)
                if data:
                    rec.write(data)
        return res

    @api.model
    def get_partners(self):
        begin = self._context.get('begin', 0)
        domain = []
        if begin > 0:
            domain = [('id', '<', begin)]
        partners = self.search(domain, limit=20, order='id desc')
        infos, types = [], {'customer': 'Khách Hàng'}
        success = False
        for partner in partners:
            begin = partner.id

            selcted = partner
            type = selcted.partner_type_id.code or 'customer'
            if partner.parent_id:
                type = 'company'
                selcted = partner.parent_id
                types.update({'company': 'Công Ty'})

            addr = selcted._display_address(True)
            if not (selcted.lat and selcted.lng):
                try:
                    if addr and len(addr) > 0:
                        data = self.get_lat_lng(addr)
                        if data:
                            selcted.write(data)
                except Exception, e:
                    True
            if selcted.partner_type_id.code and not types.get(selcted.partner_type_id.code):
                types.update({selcted.partner_type_id.code: selcted.partner_type_id.name})

            if selcted.lat and selcted.lng:
                existed_coordinate = [x for x in infos if x[1] == selcted.lat and x[2] == selcted.lng]
                if not len(existed_coordinate):
                    infos.append(['<strong>' + selcted.name + '<br>' + addr + '</strong>', selcted.lat, selcted.lng, type])

            if len(infos) > 0:
                success = True

        return {
            'data': infos,
            'success': success,
            'types': types,
            'begin': begin
        }

    def get_lat_lng(self, address):
        url = 'https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyDEkYKgpSU8xQm-2PFXCeHZT8IIlcOdmYs&address=' + address
        url = url.replace(' ', '+')
        raw = requests.get(url)
        result = raw.json()
        if result['status'] == 'OK':
            return {
                'lat': result['results'][0]['geometry']['location']['lat'],
                'lng': result['results'][0]['geometry']['location']['lng'],
            }
        else:
            return False

    @api.model
    def import_ttvh(self):
        try:
            W = px.load_workbook('/home/dham/Desktop/dhaaddon_enterprise/tgl-despacito/dha_modifier/dha_medic_gis/static/src/123123.xlsx')
            p = W.get_sheet_by_name(name='Sheet1')

            type = {
                'vh_tdtt': self.env.ref('dha_medic_gis.sports_culture_center').id,
                'văn hóa': self.env.ref('dha_medic_gis.culture_center').id,
                'tdtt': self.env.ref('dha_medic_gis.sports_center').id,
                'nhà thiếu nhi': self.env.ref('dha_medic_gis.children_house').id,
            }

            index = 0
            for row in p.iter_rows():
                if index != 0:
                    try:
                        addr = row[2].internal_value.encode('utf-8') + ',Q.' + str(row[0].internal_value)
                        data = {
                            'street': addr,
                            'name': row[1].internal_value,
                            'city_dropdown': 50,
                            'country_id': 243,
                            'partner_type_id': type.get(row[9].internal_value.encode('utf-8').strip().lower(), 1)
                        }
                        existed = self.search([('street', '=', data['street'])], limit=1)
                        if existed:
                            existed.write(data)
                        else:
                            self.create(data)
                    except Exception, e:
                        print e
                else:
                    index += 1
        except Exception:
            True