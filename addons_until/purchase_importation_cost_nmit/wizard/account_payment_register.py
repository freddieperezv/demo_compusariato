# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    import_ids = fields.Many2one(
        comodel_name='import.folder',
        string="Imports",
        readonly=False, store=True,
        compute='_compute_import_folder')

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    @api.model
    def _get_line_batch_key(self, line):
        # OVERRIDE
        # Group moves also using these additional fields.
        res = super()._get_line_batch_key(line)
        res['import_ids'] = line.move_id.import_ids.id
        return res

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('journal_id')
    def _compute_import_folder(self):
        for wizard in self:
            if wizard.can_edit_wizard:
                batches = wizard._get_batches()
                wizard.import_ids = batches[0]['payment_values']['import_ids']
            else:
                wizard.import_ids = False

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _create_payment_vals_from_wizard(self):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals['import_ids'] = self.import_ids.id
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        payment_vals['import_ids'] = batch_result['payment_values']['import_ids']
        return payment_vals
