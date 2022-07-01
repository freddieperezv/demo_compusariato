from odoo import api, fields, models


class StockPicking(models.Model):
	_inherit = "stock.picking"

	guide_ids = fields.Many2many(
		"account.remission.guide",
		string="Guides"
	)