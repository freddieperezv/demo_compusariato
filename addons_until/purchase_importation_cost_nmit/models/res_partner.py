# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from datetime import date, timedelta


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    international = fields.Boolean('International', help="This field is used in the import process, it should only be activated if it is a external supplier, when activated it will force the entry of the import folder field in the Purchase Order")
