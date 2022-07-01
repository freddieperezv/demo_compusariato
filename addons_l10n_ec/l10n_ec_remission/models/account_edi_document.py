from odoo import fields, models, api

DEFAULT_BLOCKING_LEVEL = 'error'

class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    remision_id = fields.Many2one('account.remission.guide')
    move_id = fields.Many2one('account.move', ondelete='cascade', required=False)
