# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ResCurrency(models.Model):
    _inherit = 'res.currency'


    l10n_ec_currency = fields.Char()