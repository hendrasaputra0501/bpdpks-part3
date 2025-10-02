# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class LegalCaseJenis(models.Model):
    _name = "legal.case.jenis"
    _description = "Jenis Kasus"

    name = fields.Char('Name')

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search([('name','=',rec.name),('id','!=',rec.id)]):
                raise ValidationError('Jenis Kasus %s sudah pernah diinput' % (rec.name))