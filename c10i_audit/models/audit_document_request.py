from odoo import models, fields, api

class AuditDocumentRequest(models.Model):
    _name = "audit.document.request"
    _description = "Permintaan Dokumen Audit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    audit_id = fields.Many2one('audit.audit', string='Audit', required=True, ondelete='cascade', tracking=True)
    name = fields.Char('Deskripsi Dokumen', required=True, tracking=True)
    request_date = fields.Date('Tanggal Permintaan', required=True, default=fields.Date.context_today, tracking=True)
    due_date = fields.Date('Tanggal Jatuh Tempo', required=True, tracking=True)
    division_id = fields.Many2one('hr.department', string='Divisi Teknis', tracking=True)

    document_file = fields.Binary('Lampiran Dokumen')
    document_filename = fields.Char('Nama File Dokumen')

    note = fields.Html('Catatan')

    state = fields.Selection([
        ('draft', 'draft'),
        ('submit', 'Submit'),
        ('belum_terpenuhi', 'Belum Terpenuhi'),
        ('sudah_terpenuhi', 'Sudah Terpenuhi'),
        ('diserahkan', 'Sudah Diserahkan ke Auditor'),
        ('ditolak', 'Ditolak'),
    ], string='Status', readonly=True, default='draft', tracking=True)

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_belum_terpenuhi(self):
        self.write({'state': 'belum_terpenuhi'})

    def action_sudah_terpenuhi(self):
        self.write({'state': 'sudah_terpenuhi'})

    def action_diserahkan(self):
        self.write({'state': 'diserahkan'})

    def action_ditolak(self):
        self.write({'state': 'ditolak'})
