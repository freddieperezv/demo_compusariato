# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
	_inherit = "res.partner"

	is_carrier = fields.Boolean(
		string="Is Carrier?",
		default=False
	)
	cont_especial = fields.Boolean(string="Codigo Contribuyente Especial")
	rise = fields.Boolean(string="RISE")
