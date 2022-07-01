from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # def is_valid_ruc_ec(self, vat):
    #     if self.l10n_latam_identification_type_id.id == self.env.ref(
    #             "l10n_ec.ec_dni", False).id:
    #         return self.is_valid_ci_ec(vat)
    #     return super(ResPartner, self).is_valid_ruc_ec(vat)
