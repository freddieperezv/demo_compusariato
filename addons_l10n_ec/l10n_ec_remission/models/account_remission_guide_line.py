from odoo import fields, models, api

class AccountRemissionGuideStockLine(models.Model):
	_name = "account.remission.guide.stock.line"
	_description = "Remission Guide Stock Lines"

	guide_line_id = fields.Many2one("account.remission.guide.line")
	company_id = fields.Many2one(
		'res.company', string='Company', readonly=True, 
		required=True, index=True
	)
	product_id = fields.Many2one(
		'product.product', 'Product', ondelete="cascade", 
		check_company=True, readonly=True
	)
	product_uom_id = fields.Many2one(
		'uom.uom', 'Unit of Measure', required=True, readonly=True,
		domain="[('category_id', '=', product_uom_category_id)]"
	)
	product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
	qty_done = fields.Float(
		'Done', default=0.0, copy=False,
		digits='Product Unit of Measure' 
	)
	lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", 
		check_company=True, readonly=True
	)


class AccountRemissionGuideLine(models.Model):
	_name = "account.remission.guide.line"
	_description = "Remission Guide Lines"

	@api.onchange('picking_id')
	def _onchange_pk_id(self):
		self.stock_move_lines = [(5,)]
		self.stock_move_lines = [
			i for i in 
			self.picking_id.move_line_nosuggest_ids.generate_remission_lines()
		]

	@api.onchange('picking_id', 'move_id')
	def _onchange_pk(self):
		for rec in self:
			rec.partner_id = (rec.picking_id or rec.move_id).partner_id.id

	@api.depends('picking_id')
	def _compute_invoice(self):
		[
			remmission_id.write({
				'invoice_ids': remmission_id.picking_id.sale_id.invoice_ids.ids
			}) for remmission_id  in self
		]
		

	invoice_ids = fields.Many2many(
		'account.move',
		compute='_compute_invoice'
	)

	guide_id = fields.Many2one(
		"account.remission.guide",
	)
	picking_id = fields.Many2one(
		"stock.picking",
		domain="[('state','=','done')]",
		required=True
	)
	stock_move_lines = fields.One2many(
		'account.remission.guide.stock.line',
		'guide_line_id'
	)
	move_id = fields.Many2one(
		"account.move",
		string="Invoice",
		domain="[('move_type','in',('out_invoice','in_invoice')), ('state','=','posted')]"
	)
	partner_id = fields.Many2one(
		"res.partner",
		string="Partner"
	)
	origin = fields.Char(string="Source Document")
	reason_id = fields.Many2one(
		"remission.guide.reason",
		string="Reason"
	)
	route_id = fields.Many2one(
		"account.remission.route",
		string="Route"
	)
	dau = fields.Char(string="DAU")
