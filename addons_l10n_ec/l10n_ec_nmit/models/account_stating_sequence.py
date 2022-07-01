from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AccountL10nEcStaringSec(models.Model):
    _name = 'account.l10n.ec.staring.sec'
    _description = 'Account L10n Ec Staring Sec'

    @api.constrains('doc_code_prefix', 'l10n_ec_entity', 'l10n_ec_emission')
    def _check_check_emission(self):
        for wiz in self:
            staring_sec = self.search([
                ('journal_id', '=', wiz.journal_id.id),
                ('id', '!=', wiz.id)
            ], limit=1)
            if not staring_sec: continue
            raise ValidationError(
                _('There are not staring Sec with this information')
            )

    def get_last_number(self, journal_id, l10n_latam_document_type_id):
        return self.env['account.l10n.ec.staring.sec'].search([
            ('journal_id', '=', journal_id),
            ('l10n_latam_document_type_id', '=', l10n_latam_document_type_id)
        ], limit=1).number

    journal_id = fields.Many2one('account.journal', index=True)
    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Document Type',
        auto_join=True, index=True,
    )
    number = fields.Integer()