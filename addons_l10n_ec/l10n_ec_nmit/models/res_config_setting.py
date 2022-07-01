from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_ec_env = fields.Selection([
        ('1', 'Test'),
        ('2', 'Production')
    ], string='Environment', default='1')

    wh_automatic = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('in_invoice&out_invoice', 'Customer Invoice and Vendor Bill'),
        ('', 'Never')
    ], default='in_invoice&out_invoice')


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set(
            'res.config.settings', 'l10n_ec_env', self.l10n_ec_env
        )
        IrDefault.set(
            'res.config.settings', 'wh_automatic', self.wh_automatic
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            l10n_ec_env=IrDefault.get(
                'res.config.settings', 'l10n_ec_env'
            ) or '1',
            wh_automatic=IrDefault.get(
                'res.config.settings', 'wh_automatic'
            ),
        )
        return res
