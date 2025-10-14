from odoo import models, fields

class AuditDiscussNote(models.Model):
    _name = "audit.discuss.note"
    _description = "Catatan Pembahasan Audit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'discuss_date desc, id desc'

    audit_id = fields.Many2one(
        'audit.audit',
        string='Audit',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    discuss_date = fields.Date(
        'Tanggal Pembahasan',
        required=True,
        tracking=True
    )
    discuss_note = fields.Html(
        'Catatan Pembahasan',
        required=True,
        tracking=True
    )
