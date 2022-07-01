from odoo import fields, models, api

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    always_in_totals = fields.Boolean()