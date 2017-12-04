# -*- coding: utf-8 -*-

from odoo import models, fields, api

class dha_medic_sms_list(models.Model):
    _name = 'dha.medic.sms.list'

    list_sms_ids = fields.Many2many('dha.medic.sms', 'sms_list_rel', 'list_id', 'sms_id', string='SMS')
    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
    create_date = fields.Datetime(string='Creation Date')
    contact_nbr = fields.Integer(compute="_compute_contact_nbr", string='Number of Contacts')

    def _compute_contact_nbr(self):
        contacts_data = self.env['dha.medic.sms.contact'].read_group(
            [('list_id', 'in', self.ids), ('opt_out', '!=', True)], ['list_id'], ['list_id'])
        mapped_data = dict([(c['list_id'][0], c['list_id_count']) for c in contacts_data])
        for sms_list in self:
            sms_list.contact_nbr = mapped_data.get(sms_list.id, 0)

class dha_medic_sms_contact(models.Model):
    _name = 'dha.medic.sms.contact'

    name = fields.Char(related='partner_id.name', string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    mobile = fields.Char(related='partner_id.mobile', string='Mobile')
    create_date = fields.Datetime(string='Create Date')
    list_id = fields.Many2one(
        'dha.medic.sms.list', string='SMS List',
        ondelete='cascade', required=True,
        default=lambda self: self.env['dha.medic.sms.list'].search([], limit=1, order='id desc'))
    opt_out = fields.Boolean(string='Opt Out', help='The contact has chosen not to receive sms anymore from this list')
    unsubscription_date = fields.Datetime(string='Unsubscription Date')
    message_bounce = fields.Integer(string='Bounce', help='Counter of the number of bounced sms for this contact.')

    @api.model
    def create(self, vals):
        if 'opt_out' in vals:
            vals['unsubscription_date'] = vals['opt_out'] and fields.Datetime.now()
        return super(dha_medic_sms_contact, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'opt_out' in vals:
            vals['unsubscription_date'] = vals['opt_out'] and fields.Datetime.now()
        return super(dha_medic_sms_contact, self).write(vals)