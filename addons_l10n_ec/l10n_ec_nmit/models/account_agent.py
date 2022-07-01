from odoo import fields, models, api


class AccountAgent(models.Model):
    _name = 'account.agent'
    _description = 'Agent'

    name = fields.Char()
    description = fields.Char()
    company_id = fields.Many2one('res.company')
