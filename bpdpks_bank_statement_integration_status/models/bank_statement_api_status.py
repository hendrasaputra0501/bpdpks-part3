from odoo import models, fields

class BankStatementApiStatus(models.Model):
    _name = 'bank.statement.api.status'
    _description = 'Status Log Sinkronisasi MT940'
    _order = 'date desc'

    journal_id = fields.Many2one('account.journal', string='Journal')
    date = fields.Date(string='Date')
    url = fields.Char(string='Source URL')
    status_code = fields.Integer(string='Response Code')
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('parse_error', 'Parse Error'),
    ], string='Status')
    message = fields.Text(string='Message')
