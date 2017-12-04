from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.one
    @api.depends('message_follower_ids')
    def _compute_partner_follower_text(self):
        partners = self.message_follower_ids.mapped('partner_id').sorted(key='name')
        partner_follower_char = ''
        for partner in  partners:
            if partner_follower_char == '':
                partner_follower_char += partner.name
            else:
                partner_follower_char += '\n' + partner.name
        self.partner_follower_char = partner_follower_char

    partner_follower_char = fields.Text('Followers Text', compute='_compute_partner_follower_text')
