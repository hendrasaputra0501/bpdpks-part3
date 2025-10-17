from odoo import models, fields, api
import re

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'


    # Pungutan
    number_of_pungutan = fields.Integer(string='Jumlah Pungutan', compute='_compute_statement_cluster', store=True)
    number_of_pungutan_reconciled = fields.Integer(string='Pungutan Reconciled', compute='_compute_statement_cluster', store=True)
    number_of_pungutan_recon_failed = fields.Integer(string='Pungutan Gagal Reconcile', compute='_compute_statement_cluster', store=True)
    number_of_pungutan_pending = fields.Integer(string='Pungutan Pending', compute='_compute_statement_cluster', store=True)

    # SPM
    number_of_spm = fields.Integer(string='Jumlah SPM', compute='_compute_statement_cluster', store=True)
    number_of_spm_reconciled = fields.Integer(string='SPM Reconciled', compute='_compute_statement_cluster', store=True)
    number_of_spm_recon_failed = fields.Integer(string='SPM Gagal Reconcile', compute='_compute_statement_cluster', store=True)
    number_of_spm_pending = fields.Integer(string='SPM Pending', compute='_compute_statement_cluster', store=True)

    # Bank Deposit
    number_of_bank_deposit = fields.Integer(string='Jumlah Bank Deposit', compute='_compute_statement_cluster', store=True)
    number_of_bank_deposit_reconciled = fields.Integer(string='Bank Deposit Reconciled', compute='_compute_statement_cluster', store=True)
    number_of_bank_deposit_recon_failed = fields.Integer(string='Bank Deposit Gagal Reconcile', compute='_compute_statement_cluster', store=True)
    number_of_bank_deposit_pending = fields.Integer(string='Bank Deposit Pending', compute='_compute_statement_cluster', store=True)

    # kesimpulan
    number_of_receive = fields.Integer(string='Jumlah Penerimaan', compute='_compute_statement_cluster', store=True)
    number_of_receive_reconciled = fields.Integer(string='Penerimaan Berhasil', compute='_compute_statement_cluster', store=True)
    number_of_receive_pending = fields.Integer(string='Penerimaan Pending', compute='_compute_statement_cluster', store=True)
    
    number_of_payment = fields.Integer(string='Jumlah Pengeluaran', compute='_compute_statement_cluster', store=True)
    number_of_payment_reconciled = fields.Integer(string='Pengeluaran Berhasil', compute='_compute_statement_cluster', store=True)
    number_of_payment_pending = fields.Integer(string='Pengeluaran Pending', compute='_compute_statement_cluster', store=True)

    receive_reconcile_state = fields.Selection([
        ('not_done', 'Belum Selesai'),
        ('done', 'Selesai')
    ], string='Status Rekon Penerimaan', compute='_compute_statement_cluster', store=True)

    payment_reconcile_state = fields.Selection([
        ('not_done', 'Belum Selesai'),
        ('done', 'Selesai')
    ], string='Status Rekon Pengeluaran', compute='_compute_statement_cluster', store=True)

    @api.depends('state' ,'line_ids.is_reconciled', 'line_ids.recon_failed', 'line_ids.amount', 'line_ids.ref', 'line_ids.payment_ref')
    def _compute_statement_cluster(self):
        for rec in self:
            
            if rec.state != 'posted':
                rec.number_of_receive = 0
                rec.number_of_payment = 0

                rec.number_of_spm = 0
                rec.number_of_pungutan = 0
                rec.number_of_bank_deposit = 0

                rec.number_of_pungutan_reconciled = 0
                rec.number_of_pungutan_recon_failed = 0
                rec.number_of_pungutan_pending = 0

                rec.number_of_spm_reconciled = 0
                rec.number_of_spm_recon_failed = 0
                rec.number_of_spm_pending = 0

                rec.number_of_bank_deposit_reconciled = 0
                rec.number_of_bank_deposit_recon_failed = 0
                rec.number_of_bank_deposit_pending = 0

                rec.number_of_receive_reconciled = 0
                rec.number_of_receive_pending = 0
                rec.number_of_payment_reconciled = 0
                rec.number_of_payment_pending = 0
                
                rec.receive_reconcile_state = 'done' if rec.state == 'confirm' else 'not_done'
                rec.payment_reconcile_state = 'done' if rec.state == 'confirm' else 'not_done'
                continue
                
            
            lines = rec.line_ids

            pungutan_pattern = "(99\d{2}(2[1-9]|3[1-9])(0[1-9]|1[0-2])\d{7})"


            rec.number_of_receive = len(lines.filtered(lambda l: l.amount > 0))
            rec.number_of_payment = len(lines.filtered(lambda l: l.amount < 0))

            rec.number_of_spm = len(lines.filtered(lambda l: 'SPM' in (l.payment_ref or '').upper()))
            rec.number_of_pungutan = len(lines.filtered(lambda l: re.search(pungutan_pattern, l.payment_ref or '')))
            rec.number_of_bank_deposit = len(lines.filtered(lambda l: 'DEPOSITO' in (l.payment_ref or '').upper()))

            
            rec.number_of_pungutan_reconciled = len(lines.filtered(lambda l: re.search(pungutan_pattern, l.payment_ref or '') and l.is_reconciled))
            rec.number_of_pungutan_recon_failed = len(lines.filtered(lambda l: re.search(pungutan_pattern, l.payment_ref or '') and l.recon_failed))
            rec.number_of_pungutan_pending = rec.number_of_pungutan - (rec.number_of_pungutan_reconciled + rec.number_of_pungutan_recon_failed)

            rec.number_of_spm_reconciled = len(lines.filtered(lambda l: 'SPM' in (l.payment_ref or '').upper() and l.is_reconciled))
            rec.number_of_spm_recon_failed = len(lines.filtered(lambda l: 'SPM' in (l.payment_ref or '').upper() and l.recon_failed))
            rec.number_of_spm_pending = rec.number_of_spm - (rec.number_of_spm_reconciled + rec.number_of_spm_recon_failed)


            # Masih dalam pengecekan
            rec.number_of_bank_deposit_reconciled = len(lines.filtered(lambda l: 'DEPOSITO' in (l.payment_ref or '').upper() and l.is_reconciled))
            rec.number_of_bank_deposit_recon_failed = len(lines.filtered(lambda l: 'DEPOSITO' in (l.payment_ref or '').upper() and l.recon_failed))
            rec.number_of_bank_deposit_pending = rec.number_of_bank_deposit - (rec.number_of_bank_deposit_reconciled + rec.number_of_bank_deposit_recon_failed)

            rec.number_of_receive_reconciled = len(lines.filtered(lambda l: l.amount > 0 and l.is_reconciled))
            rec.number_of_receive_pending = rec.number_of_receive - rec.number_of_receive_reconciled
            rec.number_of_payment_reconciled = len(lines.filtered(lambda l: l.amount < 0 and l.is_reconciled))
            rec.number_of_payment_pending = rec.number_of_payment - rec.number_of_payment_reconciled

            rec.receive_reconcile_state = 'done' if rec.number_of_receive_pending == 0 else 'not_done'
            rec.payment_reconcile_state = 'done' if rec.number_of_payment_pending == 0 else 'not_done'
            
    def action_open_bank_statement_form(self):
        self.ensure_one()
        return {
            'name': 'Bank Statement',
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('account.view_bank_statement_form').id, 'form')],
            'target': 'current',
        }
    
    def action_reconcile_receive(self):
        self.ensure_one()
        
        limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        
        stmt_lines = self.line_ids.filtered(lambda l: l.amount > 0 and not l.is_reconciled)[:limit]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {
                'statement_line_ids': stmt_lines.ids,
                'company_ids': self.company_id.ids
            },
        }

    def action_reconcile_payment(self):
        self.ensure_one()
        limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        stmt_lines = self.line_ids.filtered(lambda l: l.amount < 0 and not l.is_reconciled)[:limit]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {
                'statement_line_ids': stmt_lines.ids,
                'company_ids': self.company_id.ids
            },
        }

    def action_reconcile_pungutan(self):
        self.ensure_one()
        pungutan_pattern = "(99\d{2}(2[1-9]|3[1-9])(0[1-9]|1[0-2])\d{7})"
        limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        stmt_lines = self.line_ids.filtered(
            lambda l: re.search(pungutan_pattern, l.payment_ref or '') and not l.is_reconciled
        )[:limit]

        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {
                'statement_line_ids': stmt_lines.ids,
                'company_ids': self.company_id.ids
            },
        }

    def action_reconcile_spm(self):
        self.ensure_one()
        limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        stmt_lines = self.line_ids.filtered(
            lambda l: 'SPM' in (l.payment_ref or '').upper() and not l.is_reconciled
        )[:limit]

        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {
                'statement_line_ids': stmt_lines.ids,
                'company_ids': self.company_id.ids
            },
        }

    # def action_reconcile_bank_deposit(self):
        self.ensure_one()
        limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        stmt_lines = self.line_ids.filtered(
            lambda l: 'DEPOSITO' in (l.payment_ref or '').upper() and not l.is_reconciled
        )[:limit]

        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {
                'statement_line_ids': stmt_lines.ids,
                'company_ids': self.company_id.ids
            },
        }