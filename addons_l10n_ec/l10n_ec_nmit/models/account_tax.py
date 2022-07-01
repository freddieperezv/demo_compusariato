from odoo import fields, models, api
from . import utils

class AccountTax(models.Model):
    _inherit = 'account.tax'

    @property
    def l10n_ec_wh_code(self):
        """escoge ret iva / ret ir"""
        return self.tax_group_id.l10n_ec_type in (
                "withhold_vat", "withhold_income_tax"
        ) and {
            # RENTA
            -2: '327', -3: '328',
            # IVA
            -10: '9', -20: '10', -30: '1',
            -50: '11', -70: '2', -100: '3'
        }.get(self.amount) or self.l10n_ec_code_ats

    @property
    def l10n_ec_tax_code(self):
        """escoge ret iva / ret ir"""
        return self.tax_group_id.l10n_ec_type in (
                "withhold_vat", "withhold_income_tax"
        ) and {
            'withhold_income_tax': '1', 'withhold_vat': '2', 'others': '6'
        }.get(self.tax_group_id.l10n_ec_type) or ''

    @property
    def gt_account(self):
        return self.invoice_repartition_line_ids \
            and self.invoice_repartition_line_ids[-1].account_id.id \
            or False

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None,
                    partner=None, is_refund=False, handle_price_include=True,
                    include_caba_tags=False):
        if self.env.context.get("wh"):
            return super(AccountTax, self.filtered(
                lambda x: x.tax_group_id.l10n_ec_type in (
                    'withhold_vat', 'withhold_income_tax'
                ))
             ).compute_all(
                price_unit, currency, quantity, product, partner,
                is_refund, handle_price_include, include_caba_tags
            )
        elif self.env.context.get("all"):
            return super(AccountTax, self).compute_all(
                price_unit, currency, quantity, product, partner,
                is_refund, handle_price_include, include_caba_tags
            )
        return super(AccountTax, self.filtered(
                lambda x: x.tax_group_id.l10n_ec_type not in (
                    'withhold_vat', 'withhold_income_tax'
                ))
             ).compute_all(
                price_unit, currency, quantity, product, partner,
                is_refund, handle_price_include, include_caba_tags
            )
