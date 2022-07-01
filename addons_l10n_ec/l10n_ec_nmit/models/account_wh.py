import re
from odoo import api, fields, models
from . import utils

READONLY_STATE = {'readonly': False, 'states': {'posted': [('readonly', True)]}}

class AccountWithholding(models.Model):
    _inherit = [
        'account.l10n.ec.mixim', 'mail.thread', 'mail.activity.mixin',
        'sequence.mixin', 'account.l10n.ec.edi', 'account.l10n.ec.common'
    ]
    _name = 'account.wh'
    _description = 'withhonding'

    def action_draft(self):
        self.move_id.button_draft()
        self.state = 'draft'

    @api.depends(
        'partner_id', 'company_id', 'date',
        'l10n_latam_document_type_id',
        'journal_id', 'l10n_latam_document_number',
    )
    def _compute_l10n_ec_access_key(self):
        return super(AccountWithholding, self)._compute_l10n_ec_access_key()

    def action_send_ride(self):
        ride_template = self.env.ref('l10n_ec_nmit.wh_ride_template')
        ride_template.write({
            'attachment_ids': [(
                4, self.edi_document_ids.filtered(
                    lambda x: x.state == 'sent'
                ).attachment_id.id
            )]
        })
        return ride_template.send_mail(
            self.id, force_send=True
        )

    def _get_move_lines(self):
        self.ensure_one()
        move_type = self.move_type == "in_invoice"
        return [(0, 0, {
            "partner_id": self.partner_id.id,
            "account_id": (
                self.move_type == "in_invoice"
                and self.partner_id.property_account_payable_id.id
                or self.partner_id.property_account_receivable_id.id
            ),
            "name": self.name,
            "credit": 0.00 if move_type  else self.amount_total ,
            "debit": self.amount_total if move_type else  0.00
        })] + [(0, 0, {
            "partner_id": self.partner_id.id,
            "account_id": line.account_id.id,
            "name": line.tax_id.display_name,
            "credit": line.amount if move_type else 0.00,
            "debit": 0.00 if move_type else line.amount,
            'tax_tag_ids': [(6, 0, line.tax_tag_ids.ids)]
        }) for line in self.tax_line_ids]

    def _create_move(self):
        self.ensure_one()
        move_id = self.env["account.move"].create({
            "partner_id": self.partner_id.id,
            "move_type": "entry",
            "wh_id": self.id,
            "journal_id": self.journal_id.id,
            "l10n_latam_document_number": self.l10n_latam_document_number,
            "l10n_latam_document_type_id": self.l10n_latam_document_type_id.id,
            "ref": ", ".join(self.move_ids.mapped('name')),
            "date": self.date,
            "line_ids": self._get_move_lines()
        })
        self.write({"move_id": move_id.id})
        return move_id

    def create_move(self):
        move_ids = self.env["account.move"]
        self.write({"state": "posted"})
        for wh in self:
            if self.posted_before:
                move_ids |= wh.move_id
                continue
            move_ids |= wh._create_move()
        return move_ids

    def action_validate(self):
        move_ids = self.create_move()
        self.posted_before = True
        move_ids._post(soft=False)
        move_ids._reconcile_wh
        move_ids._set_edi()
        return move_ids
        
    @api.onchange("move_ids")
    def _onchange_move_id(self):
        """ Change taxes if invoice change """
        self.write({'tax_line_ids': [(5,)]})
        for wh in self:
            tax_line_ids = []
            [
                tax_line_ids.extend(move_id.invoice_line_ids._gt_wh_line())
                for move_id in wh.move_ids
            ]
            wh.tax_line_ids = tax_line_ids

    @api.depends('move_type')
    def _compute_l10n_latam_document_type(self):
        [
            rec.write({'l10n_latam_document_type_id': self.env.ref(
                rec.move_type == 'in_invoice'
                and 'l10n_ec.ec_dt_42' or 'l10n_ec_nmit.ec_dt_07'
            ).id}) for rec in self if rec.state == 'draft'
        ]

    @api.model
    def _get_default_journal(self):
        if self._context.get('default_journal_id'):
            return self.env['account.journal'].browse(
                self._context['default_journal_id']).id
        move_type = self._context.get('default_move_type', 'entry')
        if move_type == 'in_invoice': journal_types =  'purchase'
        elif move_type == 'out_invoice': journal_types = 'sale'
        else: journal_types = 'general'
        return self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type', '=', journal_types)
        ], limit=1).id


    def _domain_journal_id(self):
        move_type = {
            'in_invoice': 'purchase',
            'out_invoice': 'sale'
        }.get(self.env.context.get('default_move_type'), 'general')
        return [
            ('id', 'in', self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id or self.env.company.id),
                ('type', '=', move_type)
            ]).ids)
        ]

    @api.depends('tax_line_ids.amount')
    def _get_totals(self):
        for wh in self:
            wh.amount_total = sum(wh.tax_line_ids.mapped('amount'))

    _sequence_index = "journal_id"
    move_ids = fields.Many2many(
        "account.move", 'move_wh_rel', 'wh_id', 'move_id',
        "Relational document", required=False, copy=False,
        readonly=False, states={'posted': [('readonly', True)]},
    )
    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
    ], readonly=True)
    tax_line_ids = fields.One2many(
        "account.wh.line", "wh_id", "Tax Details", copy=False, **READONLY_STATE
    )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', ondelete='restrict',
        **READONLY_STATE, required=True
    )
    date = fields.Date(default=fields.Date.today())
    journal_id = fields.Many2one(
        'account.journal', 'Journal', required=True,
        check_company=True, domain=_domain_journal_id,
        default=_get_default_journal, **READONLY_STATE,
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company.id,
        **READONLY_STATE
    )
    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True,
        copy=False, tracking=True, default='draft'
    )
    posted_before = fields.Boolean()
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id'
    )
    amount_total = fields.Monetary(compute='_get_totals', store=True)
    edi_document_ids = fields.One2many('account.edi.document', 'wh_id')
    l10n_ec_auth_number_customer = fields.Char(string='Authoritation number')
    l10n_ec_access_key = fields.Char(
        compute='_compute_l10n_ec_access_key', store=True
    )
    edi_blocking_level = fields.Selection(related='move_id.edi_blocking_level')
    edi_error_count = fields.Integer(related='move_id.edi_error_count')
    edi_error_message = fields.Html(related='move_id.edi_error_message')
    edi_state = fields.Selection(related='move_id.edi_state')
    edi_web_services_to_process = fields.Text(
        related='move_id.edi_web_services_to_process'
    )