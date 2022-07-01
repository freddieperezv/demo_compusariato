from odoo import api, fields, models


class PayResident(models.Model):
    _name = "l10n.ec.pay.resident"
    _description = 'Pay Resident'

    name = fields.Char(string='Payment resident')
    code = fields.Char(string='Code')
    state = fields.Boolean(string='Estado', default=True, copy=False)


class TypeForeignTaxRegime(models.Model):
    _name = "l10n.ec.type.foreign.tax.regime"
    _description = 'Type Foreign Tax Regime'

    name = fields.Char(string='Type foreign tax regime')
    code = fields.Char(string='Code')
    state = fields.Boolean(string='Estado', default=True, copy=False)


class CountryPaymentRegime(models.Model):
    _name = "l10n.ec.country.payment.regime"
    _description = 'Country Payment Regime'

    name = fields.Char(string='Country Payment Regime')
    code = fields.Char(string='Code')
    state = fields.Boolean(string='Estado', default=True, copy=False)


class TaxHavenCountry(models.Model):
    _name = "l10n.ec.tax.haven.country"
    _description = 'Tax Haven Country'

    name = fields.Char(string='Haven Country')
    code = fields.Char(string='Code')
    name2 = fields.Char(string='Tax Haven Country link')
    code2 = fields.Char(string='Code 2')
    state = fields.Boolean(string='Estado', default=True, copy=False)
