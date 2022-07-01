# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import date, timedelta
from odoo.addons import decimal_precision as dp
import ast
import json


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    
    import_ids = fields.Many2one('import.folder', string="Imports")
    require_import = fields.Boolean(string="Required Import")

    @api.onchange('partner_id')
    def _require_import(self):
        for move in self:
            if move.partner_id.international:
                move.require_import = True
            else:
                move.require_import = False

    def button_confirm(self):
        self.changeMandatory()
        res = super(PurchaseOrder, self).button_confirm()
        return res


    # def button_confirm(self):
    #     self.changeMandatory()
    #     for order in self:
    #         if order.state not in ['draft', 'sent']:
    #             continue
    #         order._add_supplier_to_product()
    #         # Deal with double validation process
    #         if order.company_id.po_double_validation == 'one_step'\
    #                 or (order.company_id.po_double_validation == 'two_step'\
    #                     and order.amount_total < self.env.user.company_id.currency_id._convert(
    #                         order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
    #                 or order.user_has_groups('purchase.group_purchase_manager'):
    #             order.button_approve()
    #         else:
    #             order.write({'state': 'to approve'})
    #     return True

    #@api.constrains('partner_id')
    def changeMandatory(self):
        if self.partner_id.international == True and (self.import_ids.id == None or self.import_ids.id == False):
            raise ValidationError(_("You are using an international provider, you must assign the corresponding import folder."))

    # def action_view_invoice(self, invoices=False):
    #     res = super(PurchaseOrder, self).action_view_invoice(invoices)
    #     if self.import_ids:
    #         vals = (ast.literal_eval(res['context']))
    #         vals.update({'default_import_ids': self.import_ids.id,})
    #         res['context'] = json.dumps(vals)
    #     return res


    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.import_ids:
            res["import_ids"] = self.import_ids.id
        #res.update({'import_ids': self.import_ids.id})
        return res


      
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'import_ids': self.import_ids.id})
        return res

