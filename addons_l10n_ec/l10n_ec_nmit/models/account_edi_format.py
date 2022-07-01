from odoo import fields, models, api


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _is_required_for_invoice(self, inv):
        return self.code == 'xades_ec' and (
            inv.move_type in ("out_invoice", "out_refund") or
            inv.wh_id.move_type == 'in_invoice'
        ) or super()._is_required_for_invoice(inv)

    def _is_compatible_with_journal(self, journal):
        self.ensure_one()
        return journal.type in ('sale', 'purchase')

    def _is_embedding_to_invoice_pdf_needed(self):
        # OVERRIDE
        self.ensure_one()
        return self.code != 'xades_ec' \
               or super()._is_embedding_to_invoice_pdf_needed()

    def _needs_web_services(self):
        self.ensure_one()
        return self.code == 'xades_ec' \
               or super()._needs_web_services()


    def _post_invoice_edi(self, invs):
        self.ensure_one()
        if self.code != 'xades_ec':
            return super()._post_invoice_edi(invs)
        return invs._export_xades_ec()

    # def _is_enabled_by_default_on_journal(self, journal):
    #     self.ensure_one()
    #     if self.code != 'facturx_1_0_05':
    #         return super()._is_enabled_by_default_on_journal(journal)
    #     return False