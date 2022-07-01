from odoo import fields, models, api


class ProductProdut(models.Model):
    _inherit = 'product.product'

    @staticmethod
    def _uncharacther(code):
        return code.replace(u'%', ' ') \
            .replace(u'º', ' ') \
            .replace(u'Ñ', 'N') \
            .replace(u'ñ', 'n') \
            .replace(u'&', '&amp;') \
            .replace('\n', '')

    @property
    def l10n_ec_code(self):
        return self and \
        self.default_code and \
        self._uncharacther(self.default_code) or '001'

    @property
    def l10n_ec_description(self):
        return self._uncharacther(self.name.strip())[: 254]

