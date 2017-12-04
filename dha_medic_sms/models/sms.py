# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from ..service.sms_service import SMSService
from odoo.http import route, request
import ast
import re

class dha_medic_sms(models.Model):
    _name = 'dha.medic.sms'

    @api.model
    def _get_sms_domain(self):
        return [('id', '=', request.env.user.partner_id.id)]

    name = fields.Char('Name')
    content = fields.Text('Content',help="-Name: $(Name)\n"
             "-Address: $(Complete Address)\n"
             "-Mobile: $(Mobile)\n"
             "-Day of Birth: $(Day of Birth)\n"
             "-Email: $(Email)\n"
             "-Customer ID: $(Customer ID)")
    sent_date = fields.Datetime('Sent Date')
    res_partner = fields.Char('ResParner model', default='res.partner')
    recipients = fields.Selection([
        ('customer','Customer'),
        ('sms_list','SMS List')
    ], default='customer', string='Recipients')
    sms_domain = fields.Char(string='Domain', oldname='domain', default=_get_sms_domain)
    sms_list_ids = fields.Many2many('dha.medic.sms.list', 'sms_list_rel', 'sms_id', 'list_id', string='List')
    status_ids = fields.One2many('dha.medic.sms.status', 'sms_id', 'SMS Send Status')

    @api.multi
    def send_sms(self):
        res_partner_obj = self.env['res.partner']
        Service = SMSService()
        state = 'success'
        description = 'N/A'
        for record in self:
            # check contact
            contact_ids = []
            mobiles = []
            if record.recipients == 'customer':
                contact_ids = res_partner_obj.search(ast.literal_eval(record.sms_domain))
            elif record.recipients == 'sms_list':
                contact_ids = self.env['dha.medic.sms.contact'].search([
                    ('list_id', 'in', record.sms_list_ids.ids), ('opt_out', '!=', True)])

            for contact in contact_ids:
                if contact.mobile and contact.mobile not in mobiles:
                    try:
                        partner_id = contact
                        if contact._name == 'dha.medic.sms.contact':
                            partner_id = contact.partner_id

                        # check content
                        content = record._check_content(partner_id, record.content)

                        result = Service.send_sms(contact.mobile, content)
                        if not result.get('status'):
                            state = 'failed'
                            description =  '{}: {}'.format(result.errorcode, result.description)

                        sms_data = {
                            'state': state,
                            'sms_id': record.id,
                            'description': description,
                            'partner_id': partner_id.id
                        }
                        record.env['dha.medic.sms.status'].create(sms_data)
                        mobiles.append(contact.mobile)
                    except Exception, e:
                        print e

    def _check_content(self, partner, content):
        dynamic_fields = re.findall(r"\${([A-Za-z]+)\}", content)
        for f in dynamic_fields:
            existed_field = self.env['ir.model.fields'].search([('model', '=', 'res.partner'), ('field_description', '=', f)],limit=1)
            if not existed_field:
                raise exceptions.Warning('Trong khách hàng không có trường: ' + f)
            content = content.replace('${'+ f +'}', partner[existed_field.name])
        return content


class dha_medic_sms_status(models.Model):
    _name = 'dha.medic.sms.status'

    sms_id = fields.Many2one('dha.medic.sms', string='SMS')
    state = fields.Selection([('success', 'Success'),('failed', 'Failed')], string='State')
    partner_id = fields.Many2one('res.partner', string='Contact')
    description = fields.Char('Description')