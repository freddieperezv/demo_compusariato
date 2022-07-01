# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, timedelta

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    import_ids = fields.Many2one(
        comodel_name='import.folder',
        string="Imports")