# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TaxSupport(models.Model):
    _name = "l10n.ec.tax.support"
    _description = 'Tax Support'

    name = fields.Char(string='Tax Support')
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')
    state = fields.Boolean(string='Active', default=True, copy=False)

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '(%s) %s' % (rec.code, name)
            result.append((rec.id, name))
        return result