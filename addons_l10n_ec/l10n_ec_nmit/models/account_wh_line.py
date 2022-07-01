from odoo import fields, models, api


class WithhondinghLine(models.Model):
    _name = 'account.wh.line'
    _description = 'Withhonding line'

    @api.onchange("tax_id")
    def _onchange_tax_id(self):
        [
            whl.update({'account_id': whl.tax_id.gt_account})
            for whl in self if whl.tax_id
        ]


    wh_id = fields.Many2one('account.wh')
    currency_id = fields.Many2one(
        'res.currency', related='wh_id.company_id.currency_id'
    )
    base = fields.Monetary("Base")
    amount = fields.Monetary("Tax Amount")
    account_id = fields.Many2one(
        "account.account", string="Tax Account", required=False,
        domain=[('internal_type', 'in', ("receivable", "payable"))],
    )
    tax_id = fields.Many2one("account.tax", string="Tax", ondelete="restrict")
    move_id = fields.Many2one("account.move")
    tax_tag_ids = fields.Many2many(
        string="Tags", comodel_name='account.account.tag', ondelete='restrict',  tracking=True,
        help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports."
    )