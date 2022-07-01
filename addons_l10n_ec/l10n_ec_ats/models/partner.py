from odoo import fields, models
from functools import lru_cache

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_pay(self):
        default_pay = self.env.ref('l10n_ec_ats.pay01', raise_if_not_found=False)
        #return default_pay and default_pay.id or False
        return default_pay

    @property
    def _l10n_ec_type_doc(self):
        return {
            "ec_ruc": "04",
            "ec_dni": "05",
            # TODO: pasaporte, exterior, final
            "l10n_latam_base.ec_passport": "06",
            "l10n_latam_base.ec_unknown": "07",
            "l10n_latam_base.ec_ex": "08",
        }.get(self.external_type)

    @property
    def _l10n_ec_tp_id_prov(self):

        return {
            "l10n_ec_base.ec_ruc": "01",
            "l10n_ec_base.ec_dni": "02",
            # TODO: pasaporte
            "l10n_latam_base.ec_unknown": "03",
        }.get(self.external_type) or False

    @property
    def external_type(self):
        [partner_type_external_id] = self.l10n_latam_identification_type_id \
                .get_external_id().values()
        return partner_type_external_id

    l10n_ec_related_party = fields.Boolean(
        string="Related party")  # Parte relacionada
    l10n_ec_pay_residents_id = fields.Many2one(
        comodel_name='l10n.ec.pay.resident',
        string='Payment resident',
        default=_get_pay
        )  # pago a residente o no residente
    l10n_ec_pay_residents_id_2 = fields.Char(related='l10n_ec_pay_residents_id.code', string='l10n_ec_pay_residents_id',)  #Usado para validaciones en attrib en la vista

    l10n_ec_type_foreign_tax_regime_id = fields.Many2one(
        comodel_name='l10n.ec.type.foreign.tax.regime',
        string='Type foreign tax regime'
    )
    l10n_ec_type_foreign_tax_regime_id_2 = fields.Char(related='l10n_ec_type_foreign_tax_regime_id.code', string='l10n_ec_type_foreign_tax_regime_id',)  #Usado para validaciones en attrib en la vista

    l10n_ec_country_payment_regime_id = fields.Many2one(
        comodel_name='l10n.ec.country.payment.regime',
        string='Country to which the payment is made'
    )
    l10n_ec_tax_haven_country_id = fields.Many2one(
        comodel_name='l10n.ec.tax.haven.country',
        string='tax haven country'
    )
    l10n_ec_name_preferential_tax_regime_id = fields.Char(
        string='name_preferential_tax_regime'
    )
    l10n_ec_double_taxation_applies_id = fields.Boolean(
        string='double taxation applies'
    )
    l10n_ec_pay_subject_wthlg_id = fields.Boolean(
        string='pay subject wthlg'
    )