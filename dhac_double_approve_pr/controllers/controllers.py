# -*- coding: utf-8 -*-
from odoo import http

# class DhacDoubleApprovePr(http.Controller):
#     @http.route('/dhac_double_approve_pr/dhac_double_approve_pr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dhac_double_approve_pr/dhac_double_approve_pr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dhac_double_approve_pr.listing', {
#             'root': '/dhac_double_approve_pr/dhac_double_approve_pr',
#             'objects': http.request.env['dhac_double_approve_pr.dhac_double_approve_pr'].search([]),
#         })

#     @http.route('/dhac_double_approve_pr/dhac_double_approve_pr/objects/<model("dhac_double_approve_pr.dhac_double_approve_pr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dhac_double_approve_pr.object', {
#             'object': obj
#         })