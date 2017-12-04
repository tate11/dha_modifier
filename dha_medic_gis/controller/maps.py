# -*- coding: utf-8 -*-
from odoo import http
import json

class Academy(http.Controller):
    @http.route('/web/dham/maps/', auth='user')
    def index(self, **kw):
        context = {
            'session_info': json.dumps(http.request.env['ir.http'].session_info())
        }

        return http.request.render('dha_medic_gis.index', qcontext=context)
