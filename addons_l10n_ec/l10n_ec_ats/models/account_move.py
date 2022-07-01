from functools import lru_cache
from babel.numbers import format_decimal
from odoo import fields, models, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    
    @lru_cache()
    def _l10n_ec_ats_tax(self):
        return self._get_tax_totals(
            self.partner_id,
            self._prepare_tax_lines_data_for_totals_from_invoice(),
            self.amount_total, self.amount_untaxed, self.currency_id
        )['groups_by_subtotal'][_("Untaxed Amount")]
    
    @property
    @lru_cache()
    def _l10n_ec_ats_get_document_by_parts(self):
        return self.l10n_latam_document_number.split('-')

    def _l10n_ec_ats_get_document(self, p):
        return self._l10n_ec_ats_get_document_by_parts[p]   
        

    @lru_cache()
    def l10n_ec_gt_group(self, code):
        group_id = self.env['account.tax.group'].search([
            ('l10n_ec_type', '=', code)
        ]).id
        for line in self._l10n_ec_ats_tax():
            if line['tax_group_id'] != group_id: continue
            return line

    def _l10n_ec_amount_code(self, code, signal):
        return (self.l10n_ec_gt_group(code) or {}).get(signal, 0.00)

    @lru_cache()
    def _get_wh(self):
        return self.wh_ids.filtered( lambda x: x.state == 'posted')
    
    def _gt_wh_values(self, purchase_type=False):
        wh_id = self._get_wh()
        key = lambda line, t: f'{line.tax_id.tax_group_id.l10n_ec_type}' \
                f'{purchase_type and abs(int(line.tax_id.amount)) or ""}_{t}'
        wh_values = {}
        [
            wh_values.update({
                key(line, 'base'): line.base,
                key(line, 'amount'): line.amount
            })
            for line in wh_id.tax_line_ids
            if  line.move_id == self.id
        ]
        def get_wh_values(k):
            return wh_values.get(k) or 0.00
        return get_wh_values