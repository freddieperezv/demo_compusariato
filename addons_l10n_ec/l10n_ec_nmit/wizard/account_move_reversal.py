# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        res.update({
            'l10n_ec_auth_number_vendor': '',
            'l10n_ec_auth_number': '',
            'l10n_ec_auth_state': '',
            'l10n_ec_auth_env': '',
            'l10n_ec_auth_date': '',
            'l10n_ec_auth_sri': '',
            'l10n_ec_auth_access_key': '',
            'l10n_ec_emission_code': '',
        })
        return res