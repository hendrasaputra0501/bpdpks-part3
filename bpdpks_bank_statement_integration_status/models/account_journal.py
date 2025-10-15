from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import requests
import json
import base64
import re
from ...account_bank_statement_import_mt940_base.mt940 import MT940
from requests.exceptions import RequestException


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    def bank_statement_status(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bpdpks_bank_statement_integration_status.bank_statement_api_status_action'
        )
        
        action.update({
            'domain': [('journal_id', '=', self.id)],
            'context': {'default_journal_id': self.id},
        })
        return action
    

    def sync_bpdpks_mt940_portal(self, sync_date=False):

        for journal in self.filtered(lambda j: j.bank_statements_source == 'bpdpks_mt940_portal'):
            sync_date = sync_date or fields.Date.context_today(self)
            trans_ref = sync_date.strftime('Transaction %d/%m/%y')
            current_bank_statement = self.env['account.bank.statement'].search([
                ('name', '=', trans_ref),
                ('journal_id', '=', journal.id)
            ])
            if current_bank_statement:
                continue

            url_mt940 = False
            if journal.name=="Bank Mandiri Operasional":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/operasional/bmri/{sync_date.strftime('%Y%m')}/1220087882737MT940{sync_date.strftime('%Y%m%d')}.txt"
                # http://10.10.10.18:1361/ftp_mt940/operasional/bmri/202309/1220087882737MT94020230926.txt
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/operasional/bmri/{sync_date.strftime('%Y%m')}/1220087882737MT940{sync_date.strftime('%Y%m%d')}.txt"
            if journal.name=="Bank Mandiri Operasional":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/operasional/bmri/{sync_date.strftime('%Y%m')}/1220087882737MT940{sync_date.strftime('%Y%m%d')}.txt"
                # http://10.10.10.18:1361/ftp_mt940/operasional/bmri/202309/1220087882737MT94020230926.txt
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/operasional/bmri/{sync_date.strftime('%Y%m')}/1220087882737MT940{sync_date.strftime('%Y%m%d')}.txt"
            elif journal.name=="Bank BRI Operasional":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/operasional/bbri/{sync_date.strftime('%Y%m')}/1220087882737MT940{sync_date.strftime('%Y%m%d')}.txt"
                # http://10.10.10.18:1361/ftp_mt940/operasional/bbri/202312/032901409999303_20231203
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/operasional/bbri/{sync_date.strftime('%Y%m')}/032901409999303_{sync_date.strftime('%Y%m%d')}"
            elif journal.name=="Bank Mandiri Penerimaan":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/operasional/bmri/{sync_date.strftime('%Y%m')}/032901003585302.{sync_date.strftime('%Y%m%d')}.txt"
                # http://10.10.10.18:1361/ftp_mt940/penerimaan/bmri/202311/1220007772737MT94020231107.txt
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/penerimaan/bmri/{sync_date.strftime('%Y%m')}/1220007772737MT940{sync_date.strftime('%Y%m%d')}.txt"
            elif journal.name=="Bank BRI Penerimaan":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/penerimaan/bbri/{sync_date.strftime('%Y%m')}/032901003585302.{sync_date.strftime('%Y%m%d')}.txt"
                # http://10.10.10.18:1361/ftp_mt940/penerimaan/bbri/202311/032901003585302.20231105.txt
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/penerimaan/bbri/{sync_date.strftime('%Y%m')}/032901003585302.{sync_date.strftime('%Y%m%d')}.txt"
            elif journal.name=="Bank BNI Penerimaan":
                # url_mt940 = f"https://svcftp.bpdp.or.id/ftp_mt940/penerimaan/bbni/{sync_date.strftime('%Y%m')}/BPDP-MT940_H1-2737273727-{sync_date.strftime('%Y%m%d')}.txt"
                url_mt940 = f"http://10.10.10.18:1361/ftp_mt940/penerimaan/bbni/{sync_date.strftime('%Y%m')}/BPDP-MT940_H1-2737273727-{sync_date.strftime('%Y%m%d')}.txt"

            if not url_mt940:
                continue

            existing_log = self.env['bank.statement.api.status'].search([
                ('journal_id', '=', journal.id),
                ('date', '=', sync_date)
            ], limit=1)

            if existing_log and existing_log.status == 'success':
                continue

            try:
                response = requests.get(url_mt940)
                response_text = getattr(response, 'text', '')
                status_code = getattr(response, 'status_code', 0)

                status = 'success' if response.status_code == 200 else 'failed'
                message = response_text or str(response)

                # === Logic baru: buat atau update ===
                if not existing_log:
                    api_log = self.env['bank.statement.api.status'].create({
                        'journal_id': journal.id,
                        'date': sync_date,
                        'url': url_mt940,
                        'status_code': status_code,
                        'status': status,
                        'message': message,
                    })
                else:
                    # Kalau sudah ada log dan sebelumnya failed, update jadi success
                    if existing_log.status in ('failed', 'parse_error') and status == 'success':
                        existing_log.write({
                            'status_code': status_code,
                            'status': status,
                            'url': url_mt940,
                            'message': message,
                        })
                        api_log = existing_log
                    else:
                        # Kalau masih gagal atau error, update log-nya saja
                        existing_log.write({
                            'status_code': status_code,
                            'status': status,
                            'url': url_mt940,
                            'message': message,
                        })
                        api_log = existing_log

                if response.status_code == 200:
                    if not self._check_mt940(response.content):
                        # Update status log jika parsing gagal
                        api_log.write({
                            'status': 'parse_error',
                            'url': url_mt940,
                            'status_code': status_code,
                            'message': response_text
                        })
                        continue

                    parser = MT940()
                    if journal.name == 'Bank BNI Penerimaan':
                        currency_code, account_number, stmts_vals = parser.parse_bni(response.content, header_lines=1)
                    else:
                        currency_code, account_number, stmts_vals = parser.parse(response.content, header_lines=1)
                    stmts_vals = stmts_vals[0]

                    statement_vals = {
                        'name': trans_ref,
                        'journal_id': journal.id,
                        'balance_start': stmts_vals.get('balance_start', 0.0),
                        'balance_end_real': stmts_vals.get('balance_end_real', 0.0),
                        'date': stmts_vals.get('date', journal.next_sync_date),
                    }
                    statement_lines = []
                    for trans in stmts_vals.get('transactions', []):
                        statement_line_vals = {
                            'payment_ref': trans.get('payment_ref', ''),
                            'ref': False,
                            'amount': float(trans.get('amount', 0.0)),
                            'date': trans.get('date'),
                        }
                        bill_levy_pattern = "(99)(\d{2})(2[1-9]|3[1-9])(0[1-9]|1[0-2])(\d{7})"
                        bill_levy_number = re.search(bill_levy_pattern, trans.get('payment_ref', ''))
                        spm_um_pattern = "(SPM|UM)(\d{5})_([A-Z]+(?:_|.\d+)?)_(\d{4})"
                        spm_um_number = re.finditer(spm_um_pattern, trans.get('payment_ref', ''), re.MULTILINE)
                        if bill_levy_number:
                            statement_line_vals.update({'ref': bill_levy_number.group()})
                        elif spm_um_number:
                            code = number = dit = year = ''
                            for x, match in enumerate(spm_um_number):
                                try:
                                    code, number, dit, year = match.groups()
                                except ValueError:
                                    continue
                            statement_line_vals.update({'ref': f"{code}-{number}/{dit}/{year}"})
                        statement_lines.append((0, 0, statement_line_vals))

                    statement_vals.update({'line_ids': statement_lines})
                    new_statement = self.env['account.bank.statement'].create(statement_vals)

                    api_log.write({
                        'status': 'success',
                        'url': url_mt940,
                        'status_code': status_code,
                        'message': response_text
                    })

                    if round(new_statement.balance_end, 2) == round(statement_vals['balance_end_real'], 2):
                        new_statement.button_post()

                else:
                    api_log.write({
                        'status': 'failed',
                        'url': url_mt940,
                        'status_code': status_code,
                        'message': response_text,
                    })

            except Exception as e:
                if existing_log:
                    existing_log.write({
                        'status_code': 0,
                        'url': url_mt940,
                        'status': 'failed',
                        'message': f"Request gagal.\n{str(e)}"
                    })
                else:
                    self.env['bank.statement.api.status'].create({
                        'journal_id': journal.id,
                        'date': sync_date,
                        'url': url_mt940,
                        'status_code': 0,
                        'status': 'failed',
                        'message': f"Request gagal.\n{str(e)}"
                    })

