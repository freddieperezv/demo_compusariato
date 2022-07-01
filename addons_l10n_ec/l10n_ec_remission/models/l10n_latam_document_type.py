from odoo import fields, models, api
from odoo.osv import expression


class L10nLatamDocumentType(models.Model):

    _name = 'l10n_latam.document.type'
    _inherit = 'l10n_latam.document.type'

    internal_type = fields.Selection(
        selection_add=[('out_waybill', 'Out Waybill')]
    )
