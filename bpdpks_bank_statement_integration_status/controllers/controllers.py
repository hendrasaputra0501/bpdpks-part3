# -*- coding: utf-8 -*-
# from odoo import http


# class BpdpksBankStatementIntegrationStatus(http.Controller):
#     @http.route('/bpdpks_bank_statement_integration_status/bpdpks_bank_statement_integration_status/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bpdpks_bank_statement_integration_status/bpdpks_bank_statement_integration_status/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bpdpks_bank_statement_integration_status.listing', {
#             'root': '/bpdpks_bank_statement_integration_status/bpdpks_bank_statement_integration_status',
#             'objects': http.request.env['bpdpks_bank_statement_integration_status.bpdpks_bank_statement_integration_status'].search([]),
#         })

#     @http.route('/bpdpks_bank_statement_integration_status/bpdpks_bank_statement_integration_status/objects/<model("bpdpks_bank_statement_integration_status.bpdpks_bank_statement_integration_status"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bpdpks_bank_statement_integration_status.object', {
#             'object': obj
#         })
