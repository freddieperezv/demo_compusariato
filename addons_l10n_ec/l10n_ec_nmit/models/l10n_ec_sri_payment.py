# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SriPayment(models.Model):
    _inherit = 'l10n_ec.sri.payment'


    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '(%s) %s' % (rec.code, name)
            result.append((rec.id, name))
        return result