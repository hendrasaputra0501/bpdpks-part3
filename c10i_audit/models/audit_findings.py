from odoo import models, fields, api
from datetime import date

class AuditFindings(models.Model):
    _name = "audit.findings"
    _description = "Audit Findings"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'recommendation_date desc, id desc'

    audit_id        = fields.Many2one('audit.audit', string='Audit', ondelete='cascade', tracking=True)
    name            = fields.Char('Nomor Rekomendasi', required=True)
    condition        = fields.Text('Kondisi')
    criteria       = fields.Text('Kriteria')
    cause          = fields.Text('Sebab')
    effect         = fields.Text('Akibat')
    response      = fields.Text('Tanggapan Auditee')
    recommendation_title = fields.Char('Judul Rekomendasi', required=True)
    recommendation_date = fields.Date('Tanggal Rekomendasi', required=True)
    date_received = fields.Date('Tanggal Terima Rekomendasi')
    date_closed = fields.Date('Tanggal Closed')
    date_done_bpdp = fields.Date('Tanggal Selesai BPDP')
    division_id      = fields.Many2one('hr.department', string='Devisi Teknis')
    attachment = fields.Binary(string='Lampiran Hasil')
    attachment_name = fields.Char()
    state = fields.Selection([
        ('draft','Draft'),
        ('proses','Proses'),
        ('selesai_bpdp','Selesai BPDP'),
        ('closed','Closed'),
    ], default='draft', tracking=True)

    note = fields.Html('Catatan')
    
    def action_proses(self):
        for rec in self:
            rec.state = 'proses'
    
    def action_selesai_bpdp(self):
        today = date.today()
        for rec in self:
            rec.date_done_bpdp = today
            rec.state = 'selesai_bpdp'

    def action_closed(self):
        today = date.today()
        for rec in self:
            rec.date_closed = today
            rec.state = 'closed'
