from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'
    

    def _is_enabled_by_default_on_journal(self, journal):
        self.ensure_one()
        if self.code != 'facturx_1_0_05':
            return super()._is_enabled_by_default_on_journal(journal)
        return False