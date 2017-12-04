# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from traceback import format_exception
from sys import exc_info

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

import odoo.addons.decimal_precision as dp

class MarketingCampaignActivity(models.Model):
    _inherit = "marketing.campaign.activity"

    action_type = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('report', 'Report'),
        ('action', 'Custom Action'),
    ], 'Type', required=True, oldname="type", default="email",
        help="The type of action to execute when an item enters this activity, such as:\n"
             "- SMS: send an sms using a predefined sms template \n"
             "- Email: send an email using a predefined email template \n"
             "- Report: print an existing Report defined on the resource item and save it into a specific directory \n"
             "- Custom Action: execute a predefined action, e.g. to modify the fields of the resource record")

    sms_id = fields.Many2one('dha.medic.sms', 'SMS Template')

class MarketingCampaignSegment(models.Model):
    _inherit = "marketing.campaign.segment"

    @api.multi
    def process_segment(self):
        Workitems = self.env['marketing.campaign.workitem']
        Activities = self.env['marketing.campaign.activity']
        if not self:
            self = self.search([('state', '=', 'running')])

        action_date = fields.Datetime.now()
        campaigns = self.env['marketing.campaign']
        for segment in self:
            if segment.campaign_id.state != 'running':
                continue

            campaigns |= segment.campaign_id
            activity_ids = Activities.search([('start', '=', True), ('campaign_id', '=', segment.campaign_id.id)])

            for activity_id in activity_ids:
                if activity_id.action_type == 'sms' and segment.object_id.model == 'res.partner':
                    activity_id.sms_id.send_sms()
                    segment.state = 'done'
                    continue

            criteria = []
            if segment.sync_last_date and segment.sync_mode != 'all':
                criteria += [(segment.sync_mode, '>', segment.sync_last_date)]
            if segment.ir_filter_id:
                criteria += safe_eval(segment.ir_filter_id.domain)

            # XXX TODO: rewrite this loop more efficiently without doing 1 search per record!
            for record in self.env[segment.object_id.model].search(criteria):
                # avoid duplicate workitem for the same resource
                if segment.sync_mode in ('write_date', 'all'):
                    if segment.campaign_id._find_duplicate_workitems(record):
                        continue

                wi_vals = {
                    'segment_id': segment.id,
                    'date': action_date,
                    'state': 'todo',
                    'res_id': record.id
                }

                partner = segment.campaign_id._get_partner_for(record)
                if partner:
                    wi_vals['partner_id'] = partner.id

                for activity_id in activity_ids:
                    wi_vals['activity_id'] = activity_id.id
                    Workitems.create(wi_vals)

            segment.write({'sync_last_date': action_date})
        Workitems.process_all(campaigns.ids)
        return True
