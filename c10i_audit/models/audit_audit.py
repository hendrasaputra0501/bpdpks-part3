from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AuditStage(models.Model):
    _name = 'audit.stage'
    _description = 'Audit Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True)
    code = fields.Char(required=True) 
    sequence = fields.Integer('Sequence', default=1)
    fold = fields.Boolean('Folded in Statusbar', default=False)


class AuditTag(models.Model):
    _name = 'audit.tag'
    _description = 'Audit Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Nama tag sudah digunakan.')
    ]


class AuditAudit(models.Model):
    _name = "audit.audit"
    _description = "Audit Audit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    

    name = fields.Char('Judul Audit', required=True, tracking=True)
    no_surat = fields.Char('No Surat Tugas', required=True, tracking=True)
    auditee_id = fields.Many2one('audit.partner', string='Pihak Audit', tracking=True)
    team_leader_id = fields.Many2one('res.partner', 'Ketua Tim', required=True, tracking=True)
    date_start = fields.Date('Tanggal Mulai', required=True, tracking=True)
    date_end = fields.Date('Tanggal Selesai', required=True, tracking=True)
    audit_object = fields.Html('Object Audit', tracking=True)
    
    assignment_attachment = fields.Binary('Lampiran Surat Tugas')
    assignment_filename = fields.Char('Nama Lampiran')
    
    # Nomor dok LHP
    no_doc_lhp = fields.Char('Nomor Dokument LHP')

    # relasi ke field audit.tag
    tag_ids = fields.Many2many(
    'audit.tag',
    'audit_audit_tag_rel',   
    'audit_id',              
    'tag_id',
    string='Tags'
)


    # Entry Meeting
    entry_meeting_date = fields.Date('Tanggal Entry Meeting')
    entry_meeting_note = fields.Html('Catatan Entry Meeting')
    entry_meeting_doc = fields.Binary('Dokumen Entry Meeting')
    entry_meeting_filename = fields.Char('Nama File Entry Meeting')
    
    # Exit Meeting
    exit_meeting_date = fields.Date('Tanggal Exit Meeting')
    exit_meeting_doc = fields.Binary('Risalah Meeting')
    exit_meeting_filename = fields.Char('Nama File Exit Meeting')

    # Dokument surat tugas
    document_request_ids = fields.One2many('audit.document.request', 'audit_id', string='Permindokan Dokumen')
    discussion_ids = fields.One2many('audit.discuss.note', 'audit_id', string='Pembahasan')
    findings_ids = fields.One2many('audit.findings', 'audit_id', string='Rekomendasi')

    stage_id = fields.Many2one(
        'audit.stage',
        string='Stage',
        ondelete='restrict',
        tracking=True,
        default=lambda self: self._get_default_stage_id(),
        group_expand='_read_group_stage_ids',
    )
    stage_code = fields.Char(related='stage_id.code', store=True)

    
    def _get_default_stage_id(self):
        """Ambil stage pertama sebagai default."""
        return self.env['audit.stage'].search([], order='sequence', limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Agar semua stage tampil di statusbar meski kosong."""
        return self.env['audit.stage'].search([], order='sequence')

    def write(self, vals):
        """Override write agar bisa jalankan aksi tertentu setiap kali stage berubah."""
        res = super().write(vals)
        if 'stage_id' in vals:
            for rec in self:
                rec._on_stage_changed()
        return res

    def _on_stage_changed(self): 
        """Fungsi otomatis ketika stage berpindah.""" 
        stage = self.stage_id.name 
        if stage == 'Entry Meeting': 
            self.message_post(body=f"Audit masuk ke tahap  <b>{stage}</b>.") 
        elif stage == 'Permintaan Dokumen': 
            self.message_post(body=f"Tahap <b>{stage}</b> dimulai.") 
        elif stage == 'Pembahasan': 
            self.message_post(body=f"Tahap <b>{stage}</b> dimulai.") 
        elif stage == 'Exit Meeting': 
            self.message_post(body=f"Audit memasuki  <b>{stage}</b>.") 
        elif stage == 'Done': 
            self.message_post(body=f"Audit telah selesai.") 
        elif stage == 'Cancelled': 
            self.message_post(body=f"Audit dibatalkan.")

    
    def action_confirm(self):
        """Konfirmasi audit dari Exit Meeting menjadi Done + buat user portal auditor."""
        for rec in self:
            if rec.stage_code != 'exit':
                raise UserError(_("Audit hanya dapat dikonfirmasi ketika berada di tahap 'Exit Meeting'."))

            done_stage = self.env['audit.stage'].search([('code', '=', 'done')], limit=1)
            if not done_stage:
                raise UserError(_("Stage dengan code 'done' belum didefinisikan di master 'Audit Stage'."))

            rec.stage_id = done_stage.id

            rec._create_portal_auditor_user()
            rec.message_post(body="Audit telah dikonfirmasi dan dipindahkan ke tahap <b>Done</b>. Portal Auditor diverifikasi.")


    # Fungsi untuk membuat user portal
    def _create_portal_auditor_user(self):
        """Membuat user portal auditor secara otomatis dari partner pihak_audit_id."""
        for rec in self:
            partner = rec.auditee_id
            if not partner:
                raise UserError(_("Tidak dapat membuat user portal auditor karena 'Pihak Audit' belum diisi."))

            if not partner.email:
                raise UserError(_("Partner %s tidak memiliki email, tidak bisa dibuatkan user portal.") % partner.name)

            portal_group = self.env.ref('base.group_portal')
            audit_portal_group = self.env.ref('c10i_audit.group_audit_portal')

            user = self.env['res.users'].search([('login', '=', partner.email)], limit=1)

            if not user:
                new_user = self.env['res.users'].with_context(no_reset_password=True).create({
                    'name': partner.name,
                    'login': partner.email,
                    'email': partner.email,
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [portal_group.id, audit_portal_group.id])],
                })
                rec.message_post(body=f"Portal user <b>{partner.name}</b> berhasil dibuat dan dapat mengakses dokumen audit ini.")
            else:
                user.groups_id = [(4, audit_portal_group.id)]
                rec.message_post(body=f"Auditor <b>{partner.name}</b> sudah memiliki akun portal.")