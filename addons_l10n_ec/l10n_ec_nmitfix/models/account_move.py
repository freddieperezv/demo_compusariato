from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _get_tax_totals(
            self, partner, tax_lines_data, amount_total, amount_untaxed, currency
    ):
        res = super(AccountMove, self)._get_tax_totals(
            partner, tax_lines_data, amount_total, amount_untaxed, currency
        )
        res['groups_by_subtotal'] = {
            k: v for k, v in res['groups_by_subtotal'].items() if v != 0
        }
        return res