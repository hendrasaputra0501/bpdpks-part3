from odoo import models, fields, api, _ 

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'


    audit_public_document = fields.Boolean('Audit Public Document')