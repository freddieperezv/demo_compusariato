from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @property
    def l10n_ec_name(self):
        return self.display_name.replace('&', '&amp;')

    def _l10n_ec_direction(self):
        return f'{self.street} {self.street2}'

    #se sobrescribiò temporalmente para solventar el error en la cédula al ingresarla
    @api.constrains("vat", "country_id", "l10n_latam_identification_type_id")
    def check_vat(self):
        it_ruc = self.env.ref("l10n_ec.ec_ruc", False)
        it_dni = self.env.ref("l10n_ec.ec_dni", False)
        ecuadorian_partners = self.filtered(
            lambda x: x.country_id == self.env.ref("base.ec")
        )
        
        return super(ResPartner, self - ecuadorian_partners).check_vat()