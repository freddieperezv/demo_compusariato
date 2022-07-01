# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError,UserError
from datetime import date, timedelta
from odoo.addons import decimal_precision as dp
from odoo.addons.stock_landed_costs.models import product
import collections

class stockPicking(models.Model):
    _inherit = 'stock.picking'
    
    import_ids = fields.Many2one('import.folder','Imports')


class LandedCost(models.Model):
    _name = 'stock.landed.cost'
    _inherit = 'stock.landed.cost'


    @api.onchange('picking_ids','import_ids')
    def _get_product_domain(self):
        if self.import_ids :
            stock = self.import_ids.mapped('stock_ids').mapped('id')
            if stock:
                return  {'domain':{'picking_ids':[('id', 'in', stock)]}}
            else:
                return  {'domain':{'picking_ids':[('id', 'in', [])]}}

    picking_ids = fields.Many2many(
        'stock.picking', 
        string='Transfers',
        copy=False, 
        states={'done': [('readonly', True)]},domain=_get_product_domain)

    import_ids = fields.Many2one(
        'import.folder',
        'Imports', 
        states={'done': [('readonly', True)]})

    cost_lines = fields.One2many(
        'stock.landed.cost.lines', 
        'cost_id', 
        'Cost Lines',
        copy=True, 
        states={'done': [('readonly', True)]})


    def fieldEmpty(self):
        if len(self.picking_ids) == 1:
            return True
        else:
            return False

    def invoiceExists(self,inv=None):
        if inv != None:
            invoice = self.env['stock.landed.cost.lines'].search([('invoice_id','=',inv)])
            for inv in invoice:
                if inv.id :
                    return True
                else:
                    return False       
                
    @api.onchange('picking_ids')
    def fillLines(self):
        if self.fieldEmpty():
            for inv in self.picking_ids.import_ids.invoice_ids:    
                if inv.state in ('posted'): #anteriormente usado->('open','paid'):                       
                    for line in inv.invoice_line_ids:
                        if line.product_id.landed_cost_ok and line.product_id.product_tmpl_id.type == 'service' and line.product_id.product_tmpl_id.purchase_ok and not self.invoiceExists(inv.id):
                            self.cost_lines = [(0,0,{'product_id':line.product_id.id,
                                                    'name':line.product_id.product_tmpl_id.name,
                                                    'account_id':line.product_id.product_tmpl_id.property_account_expense_id.id if line.product_id.product_tmpl_id.property_account_expense_id.id  else line.product_id.product_tmpl_id.categ_id.property_account_expense_categ_id.id,                                    
                                                    'price_unit':line.price_subtotal,                                                   
                                                    'split_method': line.product_id.product_tmpl_id.split_method_landed_cost if line.product_id.product_tmpl_id.split_method_landed_cost else 'equal',
                                                    'invoice_id': inv.id,
                                                    'cost_id':self._origin.id, 
                                                    })]      
        if not self.picking_ids:
            self.cost_lines.unlink()

   

class LandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'
    _description = 'Stock Landed Cost Line'

    invoice_id = fields.Many2one('account.move', 'Invoice')