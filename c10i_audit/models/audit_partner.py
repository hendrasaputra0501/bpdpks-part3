from odoo import models, fields, api

class AuditPartner(models.Model):
    _name = "audit.partner"
    _description = "Audit Partner"

    name = fields.Char('Nama Partner', required=True)
    alamat = fields.Text('Alamat')
    phone = fields.Char('No Telepon')
    email = fields.Char('Email')
    contact_person = fields.Char('Contact Person')