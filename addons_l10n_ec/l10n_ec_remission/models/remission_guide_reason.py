from odoo import fields, models


class RemissionGuideReason(models.Model):
	_name = "remission.guide.reason"
	_description = "Remission Guide Reason"

	name = fields.Char(string="Name")
