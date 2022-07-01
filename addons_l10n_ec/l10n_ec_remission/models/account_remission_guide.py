from odoo import api, fields, models
from odoo.exceptions import UserError

READONLY_STATE = {'readonly': False, 'states': {'posted': [('readonly', True)]}}

class AccountRemissionGuide(models.Model):
	_name = "account.remission.guide"
	_description = "Remission Guides"
	_inherit = [
        'account.l10n.ec.mixim', 'mail.thread', 'mail.activity.mixin',
        'sequence.mixin', 'account.l10n.ec.common', 'account.l10n.ec.edi'
    ]
	
	def unlink(self):
		if 'posted' in self.mapped('state'):
			raise UserError("Can't delete posted Remission Guide!")
		return super(AccountRemissionGuide, self).unlink()
		

	def _get_starting_sequence(self):
		if (
            self.journal_id.type == 'general'
            and self.company_id.country_id.code == "EC"
            and self.l10n_latam_document_type_id
        ):
			return self._get_ec_formatted_sequence()
		return super()._get_starting_sequence()

	def button_draft(self):
		return self.write({"state": "draft"})

	def button_validate(self):
		self.write({"state": "posted", "posted_before": True})
		self.with_context({
			'edi_template': 'l10n_ec_remission.remission'
		})._export_xades_ec()
		return True

	def button_cancel(self):
		pass
	
	@api.depends('name')
	def _compute_l10n_latam_document(self):
		l10n_ec_remission = self.env.ref('l10n_ec_remission.ec_dt_06').id
		self.write({
			'l10n_latam_document_type_id': l10n_ec_remission
		})

	def _domain_journal_id(self):
		return [
			('id', 'in', self.env['account.journal'].search([
				('company_id', '=', self.company_id.id or self.env.company.id),
				('type', '=', 'general')
			]).ids)
		]

	@api.model
	def _get_default_journal(self):
		if self._context.get('default_journal_id'):
			return self.env['account.journal'].browse(
				self._context['default_journal_id']).id
		return self.env['account.journal'].search([
			('company_id', '=', self.env.company.id),
			('type', '=', 'general')
		], limit=1).id

	@api.onchange('company_id')
	def _onchange_company(self):
		self.address_from = self.company_id.partner_id._l10n_ec_direction()
	
	
	def action_retry_edi_documents_error(self):
		self.with_context({
			'edi_template': 'l10n_ec_remission.remission'
		})._export_xades_ec()

	@api.depends(
        'partner_id', 'company_id', 'date',
        'l10n_latam_document_type_id',
        'journal_id', 'l10n_latam_document_number',
    )
	def _compute_l10n_ec_access_key(self):
		return super(AccountRemissionGuide, self)._compute_l10n_ec_access_key()

	def _export_xades_ec(self):
		res = super(AccountRemissionGuide, self)._export_xades_ec()
		for k, v in res.items():
			error = v.get('error', '') and 1 or 0
			k.write({
				'edi_document_ids': [(0, 0, {
					'attachment_id': v.get('attachment').id,
					'edi_format_id': self.env.ref('l10n_ec_nmit.edi_xades_ec').id,
					'error': v.get('error', ''),
					'state': v.get('error') and 'to_send' or 'sent'
				})],
				'edi_error_count': error,
				'edi_blocking_level': error and 'error' or False,
				'edi_error_message': v.get('error', ''),
			})
		return res

	@api.depends('journal_id', 'date')
	def _compute_highest_name(self):
		for record in self:
			record.highest_name = record._get_last_sequence()
	
	move_type = 'entry'
	_sequence_index = "journal_id"
	l10n_ec_access_key = fields.Char(
        compute='_compute_l10n_ec_access_key', store=True
    )
	l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', 
		compute='_compute_l10n_latam_document',
		store=True, string='Document Type'
    )
	name = fields.Char(
		copy=False, **READONLY_STATE,
		compute='_compute_name', store=True
	)
	posted_before = fields.Boolean()

	journal_id = fields.Many2one(
        'account.journal', 'Journal', required=True,
        check_company=True, domain=_domain_journal_id,
        default=_get_default_journal, **READONLY_STATE,
    )
	partner_id = fields.Many2one(
		"res.partner", **READONLY_STATE,
		string="Carrier",
		required=True,
		domain="[('is_carrier','=','True')]"
	)
	company_id = fields.Many2one(
		"res.company", **READONLY_STATE,
		default=lambda self: self.env.company.id
	)
	date = fields.Date(
		string="Fecha", **READONLY_STATE,
		default=fields.date.today()
	)
	date_start = fields.Date(
		string="Date start",
		required=True, **READONLY_STATE,
		default=fields.Date.today()
	)
	date_end = fields.Date(
		string="Date end",
		required=True, **READONLY_STATE,
		default=fields.Date.today()
	)
	license_plate = fields.Char(
		string="License Plate",
		required=True, **READONLY_STATE,
	)
	state = fields.Selection(selection=[
        ('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True,
        copy=False, tracking=True, default='draft'
    )
	address_from = fields.Char()
	line_ids = fields.One2many(
		"account.remission.guide.line",
		"guide_id", **READONLY_STATE,
		string="Lines"
	)
	edi_document_ids = fields.One2many(
       'account.edi.document', 'remision_id'
    )
	highest_name = fields.Char(compute='_compute_highest_name')