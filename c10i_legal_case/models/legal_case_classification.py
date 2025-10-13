# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class LegalCaseClassification(models.Model):
    _name = "legal.case.classification"
    _description = "Klasifikasi"

    name = fields.Char('Name')

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search([('name','=',rec.name),('id','!=',rec.id)]):
                raise ValidationError('Klasifikasi %s sudah pernah diinput' % (rec.name))