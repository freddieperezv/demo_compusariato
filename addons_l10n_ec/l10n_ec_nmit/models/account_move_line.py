from collections import defaultdict
from functools import lru_cache
from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _gt_vat0(self):
        vat0 = self.env.ref('l10n_ec.1_tax_vat_415')
        return sum(
            line_id.price_subtotal
            for line_id in self
            if vat0 in line_id.tax_ids
        )
    
    @property
    def l10n_ec_discount(self):
        dst = (
            self.price_unit - (
                self.price_unit * (1 - (self.discount or 0.00) / 100.0)
           )
        ) * self.quantity
        return f'{dst:.2f}'


    @property
    @lru_cache()
    def _vat_code(self):
        return {
            'zero_vat': '2',
            'vat12': '2',
            'ice': '3',
            'irbpnr': '5'
            }
    @property
    @lru_cache()            
    def _vat_code_porcent(self):
        return {
            'zero_vat': '0',
            'vat12': '2',
            'not_charged_vat': '6',
            'exempt_vat': '7'
            }

    @property
    @lru_cache()
    def _l10n_ec_total_taxes_dct(self):
        irbp = self.tax_group_id.l10n_ec_type == 'irbp'
        return {
            'code': self._vat_code.get(self.tax_group_id.l10n_ec_type),
            'code_porcent': self._vat_code_porcent.get(self.tax_group_id.l10n_ec_type),
            'base': '{:.2f}'.format(abs(self.tax_base_amount)),
            'tarifa': irbp and '0.02' or abs(self.tax_line_id.amount),
            'value': '{:.2f}'.format(abs(self.price_total))
        }

    def l10n_ec_total_taxes(self, code):
        return self._l10n_ec_total_taxes_dct.get(code)

    @property
    def l10n_ec_line_taxes(self):
        for tax in self.tax_ids:
            irbp = tax.tax_group_id.l10n_ec_type == 'irbp'
            if 'withhold' in tax.tax_group_id.l10n_ec_type: continue
            yield {
                'type': tax.tax_group_id.l10n_ec_type,
                'codigo': self._vat_code.get(tax.tax_group_id.l10n_ec_type),
                'codigoPorcentaje': self._vat_code_porcent.get(tax.tax_group_id.l10n_ec_type),
                'tarifa': irbp and f'{self.price_subtotal:.2f}' or
                          abs(tax.amount),
                'baseImponible': f'{self.price_subtotal:.2f}',
                'valor': '{:.2f}'.format(irbp and  tax._compute_amount(
                        self.price_subtotal, self.price_unit, self.quantity,
                        self.product_id
                    ) or self.price_subtotal * abs(tax.amount) / 100.0
                )
            }.get

    def _compute_taxes(self):
        """Computes Withholding Taxes """
        amount_discunted = (self.move_id.is_inbound() and -1 or 1) * (
                self.price_unit * (1 - (self.discount / 100.0)
           )
        )
        return self.tax_ids._origin.with_context(
            force_sign=self.move_id._get_tax_force_sign()
        ).with_context(wh=True).compute_all(
            amount_discunted, currency=self.currency_id,
            quantity=self.quantity, product=self.product_id,
            partner=self.partner_id,
            is_refund=self.move_id.move_type in ("out_refund", "in_refund"),
            handle_price_include=True,
        )

    def _gt_wh_line(self):
        account_tax = self.env["account.tax"]
        res = defaultdict(lambda : defaultdict(float))
        repartition_line = self.env["account.tax.repartition.line"]
        for line in self:
            for tax in line._compute_taxes()["taxes"]:
                tax_group_id = account_tax.browse(tax["id"]).tax_group_id
                tax_repartition_line_id = repartition_line.browse(
                    tax["tax_repartition_line_id"]
                )
                tax_id = tax_repartition_line_id.invoice_tax_id \
                         or tax_repartition_line_id.refund_tax_id
                tax_base = (
                    (tax_group_id.l10n_ec_type == "withhold_vat" and 0.12 or 1)
                    * abs(tax["base"])
                )

                if (tax_id.id, line.move_id.id) not in res:
                    res[(tax_id.id, line.move_id.id)]["account_id"] = \
                        tax_repartition_line_id.account_id.id
                    res[(tax_id.id, line.move_id.id)]["tax_tag_ids"] = \
                        tax_repartition_line_id.tag_ids.ids
                res[(tax_id.id, line.move_id.id)]["amount"] += abs(tax["amount"])
                res[(tax_id.id, line.move_id.id)]["base"] += (
                    line.currency_id != line.company_currency_id
                    and line.company_currency_id._convert(
                        tax_base, line.currency_id, line.company_id,
                        line.date or fields.Date.context_today(self)
                    ) or tax_base
                )
        return [
            (0, 0, {
                "tax_id": tax_id,
                "move_id": move_id,
                "account_id": vals["account_id"],
                "tax_tag_ids": [(6, 0, vals["tax_tag_ids"])],
                "amount": vals["amount"],
                "base": vals["base"],
            }) for (tax_id, move_id), vals in res.items()
        ]