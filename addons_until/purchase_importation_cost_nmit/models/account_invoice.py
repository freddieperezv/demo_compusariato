# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import date, timedelta
import json


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'
    
    import_ids = fields.Many2one('import.folder', string="Imports")
    require_import = fields.Boolean(string="Required Import")

    @api.onchange('partner_id')
    def _require_import(self):
        for move in self:
            if move.move_type == 'in_invoice' and move.partner_id.international:
                move.require_import = True
            else:
                move.require_import = False

    def action_post(self):
        self.changeMandatory()
        res = super(AccountMove, self).action_post()
        return res

    def changeMandatory(self):
        for lines in self.invoice_line_ids:
            if lines.account_id.international == True and (self.import_ids == None or not self.import_ids.id) and self.move_type == 'in_invoice':
                raise ValidationError(_("You are using account that is used for imports, you must assign the corresponding import folder to confirm the document."))

    #Asigna la carpeta en el pago cuando se añade el pago a la factura (desde la factura)
    def _get_reconciled_vals(self, partial, amount, counterpart_line):
        result = super()._get_reconciled_vals(partial, amount, counterpart_line)
        result['import_ids'] = self.import_ids.id
        return result


class AccountAccount(models.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    international = fields.Boolean('International', help="This field is used in the import process, it should only be activated if, when using this accounting account, you must request the mandatory entry of the import folder field in the supplier invoice")

    

