from odoo import api, fields, models


class SaleOrder(models.Model):
	_inherit = "sale.order"

	guide_ids = fields.Many2many(
		"account.remission.guide",
		string="Guides"
	)