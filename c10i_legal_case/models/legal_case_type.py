# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class LegalCaseType(models.Model):
    _name = "legal.case.type"
    _description = "Tags"

    name = fields.Char('Name')

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search([('name','=',rec.name),('id','!=',rec.id)]):
                raise ValidationError('Tags %s sudah pernah diinput' % (rec.name))