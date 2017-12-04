# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, config
import StringIO
from collections import deque
import os
import uuid
from odoo.exceptions import UserError, ValidationError


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.constrains('start_datetime', 'stop_datetime', 'start_date', 'stop_date','resource_ids')
    def _check_closing_date(self):
        for meeting in self:
            if meeting.start_datetime and meeting.stop_datetime and meeting.stop_datetime < meeting.start_datetime:
                raise ValidationError(_('Ending datetime cannot be set before starting datetime.'))
            if meeting.start_date and meeting.stop_date and meeting.stop_date < meeting.start_date:
                raise ValidationError(_('Ending date cannot be set before starting date.'))
            if meeting.resource_ids:
                if meeting.start_datetime and meeting.stop_datetime:
                    duplicate = self.sudo().with_context({'virtual_id': True}).search(
                        ['&', '|', '&', ('start', '<', meeting.stop_datetime),
                         ('start', '>=', meeting.start_datetime), '&',
                         ('stop', '<', meeting.stop_datetime), ('stop', '>=', meeting.start_datetime),
                         '&',('resource_ids', 'in',meeting.resource_ids.ids),('id','!=', meeting.id)])
                    if duplicate :
                        raise ValidationError(_('Resource have been used.'))
