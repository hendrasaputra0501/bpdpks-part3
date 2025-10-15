# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bpdpks_bank_statement_integration_status(models.Model):
#     _name = 'bpdpks_bank_statement_integration_status.bpdpks_bank_statement_integration_status'
#     _description = 'bpdpks_bank_statement_integration_status.bpdpks_bank_statement_integration_status'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
