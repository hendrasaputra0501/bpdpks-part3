# -*- coding: utf-8 -*-
# from odoo import http


# class C10iAudit(http.Controller):
#     @http.route('/c10i_audit/c10i_audit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/c10i_audit/c10i_audit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('c10i_audit.listing', {
#             'root': '/c10i_audit/c10i_audit',
#             'objects': http.request.env['c10i_audit.c10i_audit'].search([]),
#         })

#     @http.route('/c10i_audit/c10i_audit/objects/<model("c10i_audit.c10i_audit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('c10i_audit.object', {
#             'object': obj
#         })
