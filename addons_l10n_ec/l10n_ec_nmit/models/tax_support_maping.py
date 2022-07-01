# -*- coding: utf-8 -*-

from odoo import api, fields, models

class TaxSupportMapping(models.Model):
    _name = "l10n.ec.tax.support.mapping"
    _description = 'Support Mapping'

    doc_type_id = fields.Many2one(
        comodel_name ='l10n_latam.document.type',
        string='Document type'
    )

    tax_support_id = fields.Many2one(
        comodel_name ='l10n.ec.tax.support',
        string='Tax support'
    ) 

    identification_type_ids = fields.Char(string='Identification allowed')

    state = fields.Boolean(string='Active', default=True, copy=False)

    def name_get(self):
        result = []
        for rec in self:
            name = rec.tax_support_id.name  
            if rec.tax_support_id.code:
                name = '(%s) %s' % (rec.tax_support_id.code, name)
            result.append((rec.id, name))
        return result
