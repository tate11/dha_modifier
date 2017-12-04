# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DhaDashboard(http.Controller):
    @http.route('/dha_dashboard/data', type='json', auth='user')
    def get_dashboard_data_js(self, **kw):
        PR = request.env['purchase.request']
        PO = request.env['purchase.order']
        LR = request.env['hr.holidays']

        res = {'pr': {}, 'po': {}, 'lr':{}}

        # Get PR DATA
        res['pr']['need_approve_domain'] = ['|', '&', ('state', '=', 'draft'), ('assigned_to', '=', request.uid), '&',
                                            ('state', '=', 'to_approve'),
                                            ('master_approver', '=', request.uid)]
        res['pr']['need_approve'] = PR.search_count(res['pr']['need_approve_domain'])
        res['pr']['last_pending_list'] = []
        if res['pr']['need_approve'] > 0:
            res['pr']['last_pending_list'] = PR.search_read(res['pr']['need_approve_domain'],
                                                            ['name', 'id', 'requested_by', 'create_date', 'dash_info',
                                                             'origin'], order='create_date desc', limit=5)

        # Get PO DATA
        res['po']['need_approve_domain'] = [('state', 'in', ('to approve', 'accepted'))]
        res['po']['need_approve'] = PO.search_count(res['po']['need_approve_domain'])
        res['po']['last_pending_list'] = []
        if res['po']['need_approve'] > 0:
            res['po']['last_pending_list'] = PO.search_read(res['po']['need_approve_domain'],
                                                            ['name', 'id', 'create_date', 'dash_info'],
                                                            order='create_date desc', limit=5)
        # Get LR DATA
        res['lr']['need_approve_domain'] = [('state', 'in', ('validate1', 'confirm')),('user_manager_id','=',request.uid)]
        res['lr']['need_approve'] = LR.search_count(res['lr']['need_approve_domain'])
        res['lr']['last_pending_list'] = []
        if res['lr']['need_approve'] > 0:
            res['lr']['last_pending_list'] = LR.search_read(res['lr']['need_approve_domain'],
                                                            ['name', 'id', 'create_date', 'dash_info'],
                                                            order='create_date desc', limit=5)
        return res
