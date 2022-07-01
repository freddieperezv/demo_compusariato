import markupsafe
import logging
from itertools import count
from itertools import groupby
from odoo import fields, models, api

logger = logging.getLogger(__name__)


class AccountAts(models.Model):
    _name = 'account.ats'
    _description = 'Account Ats'

    @staticmethod
    def set_counter():
        return count(0)

    @staticmethod
    def _next(counter):
        return next(counter)

    @property
    def _get_records(self):
        ec_dt_01 = self.env.ref('l10n_ec.ec_dt_01').id
        ec_dt_16 = self.env.ref('l10n_ec.ec_dt_16').id
        return groupby(
            self.env['account.move'].search([
                ('move_type', 'in', ('out_invoice', 'in_invoice')),
                ('state', 'in', ('posted', 'annull')),
                ('l10n_latam_document_type_id', 'in', (ec_dt_01, ec_dt_16))
                #('journal_id', '=', self.journal_id.id)
                #('journal_id.l10n_ec_entity', '=', self.l10n_ec_entity)
            ], order='state DESC, move_type ASC, date ASC'),
            lambda x: (x.state, x.move_type)
        )

    @property
    def _get_data(self):
        xml_content = markupsafe.Markup(
            "<?xml version='1.0' encoding='UTF-8'?>\n"
        )

        xml_content += self.env.ref(
            'l10n_ec_ats.ats_template')._render({'ats': self})

        return xml_content

    def action_generate_ats(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': f'/web/export/{self.id}'
        }

    name = fields.Date(string="Date")
    journal_id = fields.Many2one('account.journal')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )
    l10n_ec_entity = fields.Char(
        string="Emission Entity", size=3, default="001")
