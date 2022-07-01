from odoo import api, fields, models


class AccountMove(models.Model):
	_inherit = "account.move"

	guide_ids = fields.Many2many(
		"account.remission.guide",
		string="Guides"
	)