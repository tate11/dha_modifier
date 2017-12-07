# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import logging
from bs4 import BeautifulSoup
_logger = logging.getLogger(__name__)


class PartnerCompanyCheck(models.Model):
    _inherit = 'res.partner.company.check'

    @api.multi
    def action_show_check_list(self):
        action = self.env.ref('dha_medic_modifier.medic_medical_bill_action').read()[0]
        action['domain'] = [('id', 'in', self.medical_ids.ids)]
        return action