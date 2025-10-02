# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class LegalCaseCase(models.Model):
    _name = "legal.case.case"
    _description = "Kasus"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('No. Perkara', required=True)
    tipe_panggilan = fields.Selection([('Pemeriksaan','Pemeriksaan'),('Pengadilan','Pengadilan')],string='Tipe Panggilan', required=True, default='Pemeriksaan')
    jenis_perkara_id = fields.Many2one('legal.case.jenis', string='Jenis Perkara', required=True)
    classification_id = fields.Many2one('legal.case.classification', string='Klasifikasi', required=True)
    state_id = fields.Many2one('res.country.state', string='Lokasi')
    city = fields.Char('Kota/Kabupaten')
    tag_ids = fields.Many2many('legal.case.type', 'legal_case_legal_case_type', string='Tags')
    pemeriksa = fields.Char('Pemeriksa')
    terperiksa = fields.Char('Terperiksa')
    penggugat = fields.Char('Penggugat')
    tergugat = fields.Char('Tergugat')
    obyek_perkara = fields.Char('Obyek Perkara')
    nilai_pungutan = fields.Float('Nilai Pungutan')
    notes = fields.Text('Catatan')
    child_ids = fields.One2many('legal.case.case','parent_id', string='Child Cases')
    parent_id = fields.Many2one('legal.case.case', string='Parent Case')
    state = fields.Selection([('open','Open'),('closed','Closed')],string='State', default='open')

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search([('name','=',rec.name),('id','!=',rec.id)]):
                raise ValidationError('Klasifikasi %s sudah pernah diinput' % (rec.name))