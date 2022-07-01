# -*- coding: utf-8 -*-
# © 2016 Cristian Salamea <cristian.salamea@ayni.com.ec>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.TransientModel):

    _inherit = 'account.payment.register'

    date_to = fields.Date('Fecha Cobro')
    number = fields.Integer('Numero de Cheque')
    bank = fields.Many2one('res.bank','Banco del Cheque')
    check_type = fields.Selection([('posfechado','Posfechado'),
                                    ('dia','Al dia')], string="Tipo" , default='dia')

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals['date_to'] = self.date_to
        payment_vals['number'] = self.number
        payment_vals['bank'] = self.bank.id
        payment_vals['check_type'] = self.check_type
        return payment_vals