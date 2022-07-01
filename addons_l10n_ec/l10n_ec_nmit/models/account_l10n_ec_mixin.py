from collections import defaultdict
from odoo import fields, models, api

class L10nMxin(models.AbstractModel):
    _name = 'account.l10n.ec.mixim'

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        if not self.date or not self.journal_id:
            return "WHERE FALSE", {}
        where_string = "WHERE journal_id = %(journal_id)s AND name != '/'"
        param = {'journal_id': self.journal_id.id}
        # if not relaxed:
        #     domain = [
        #         ('journal_id', '=', self.journal_id.id),
        #         ('id', '!=', self.id or self._origin.id),
        #         ('name', 'not in', ('/', False)),
        #         ('date', '<=', self.date)
        #     ]
        #     reference_move_name = self.search(
        #         domain, order='date desc', limit=1
        #     ).name
        #     if not reference_move_name:
        #         reference_move_name = self.search(domain, order='date asc', limit=1).name
        #     sequence_number_reset = self._deduce_sequence_number_reset(reference_move_name)
        #     if param.get('anti_regex') and not self.journal_id.sequence_override_regex:
        #         where_string += " AND sequence_prefix !~ %(anti_regex)s "
        return where_string, param

    def _get_ec_formatted_sequence(self, number=0):
        return "%s %s-%s-%09d" % (
            self.l10n_latam_document_type_id.doc_code_prefix,
            self.journal_id.l10n_ec_entity,
            self.journal_id.l10n_ec_emission,
            number,
        )

    def _get_starting_sequence(self):
        if (
            self.journal_id.l10n_latam_use_documents
            and self.company_id.country_id.code == "EC"
            and self.l10n_latam_document_type_id
        ):
            return self._get_ec_formatted_sequence()
        return super()._get_starting_sequence()

    def _set_next_sequence(self):
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()
        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            seq = self.env['account.l10n.ec.staring.sec'].get_last_number(
                self.journal_id.id,
                self.l10n_latam_document_type_id.id
            )
            format_values['seq'] =  seq and (seq - 1) or 0
            format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
            format_values['month'] = self[self._sequence_date_field].month
        format_values['seq'] = format_values['seq'] + 1
        self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()
    
    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        journal_key = lambda move: (
            move.journal_id, move.journal_id.refund_sequence and move.move_type
        )
        date_key = lambda move: (move.date.year, move.date.month)
        grouped = defaultdict(
            lambda: defaultdict(
                lambda: {
                    'records': self.env[self._name],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.id))
        highest_name = self[0]._get_last_sequence() if self else False
        for move in self:
            if not highest_name and move == self[0] and not move.posted_before and move.date:
                pass
            elif (move.name and move.name != '/') or move.state != 'posted':
                try:
                    if not move.posted_before: move._constrains_date_sequence()
                    continue
                except ValidationError: pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group['records']:
                move._set_next_sequence()
                group['format'], group['format_values'] = move._get_sequence_format_param(
                    move.name
                )
                group['reset'] = move._deduce_sequence_number_reset(move.name)
            group['records'] += move
        # final_batches = []
        # for batch in final_batches:
        #     for move in batch['records']:
        #         move.name = batch['format'].format(**batch['format_values'])
        #         batch['format_values']['seq'] += 1
        #     batch['records']._compute_split_sequence()
        self.filtered(lambda m: not m.name).name = '/'

    @api.depends('l10n_latam_document_type_id', 'journal_id')
    def _is_manual_document_number(self):
        [
            rec.update({
                'l10n_latam_manual_document_number':
                    rec.journal_id.type == 'sale'
            }) for rec in self
        ]

    @api.depends('name')
    def _compute_l10n_latam_document_number(self):
        for rec in self:
            if (
                    not rec.l10n_latam_document_type_id.doc_code_prefix
                    or rec.name == '/'
            ):
                rec.l10n_latam_document_number = False
                continue
            rec.l10n_latam_document_number = rec.name.split(" ", 1)[-1]

    def _inverse_l10n_latam_document_number(self):
        for rec in self:
            if not rec.l10n_latam_document_type_id: continue
            if not rec.l10n_latam_document_number:
                rec.name = '/'
                continue
            l10n_latam_document_number = rec.l10n_latam_document_type_id\
                ._format_document_number(rec.l10n_latam_document_number)
            if rec.l10n_latam_document_number != l10n_latam_document_number:
                rec.l10n_latam_document_number = l10n_latam_document_number
            rec.name = f"{rec.l10n_latam_document_type_id.doc_code_prefix} " \
                       f"{l10n_latam_document_number}"

    def _compute_l10n_latam_document_type(self):
        self.l10n_latam_document_type_id = False

    name = fields.Char(compute='_compute_name', store=True)
    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Document Type',
        auto_join=True, index=True,
        compute='_compute_l10n_latam_document_type', store=True)
    l10n_latam_manual_document_number = fields.Boolean(
        'Manual Number', compute='_is_manual_document_number',
    )
    l10n_latam_document_number = fields.Char(
        compute='_compute_l10n_latam_document_number',
        inverse='_inverse_l10n_latam_document_number',
        string='Document Number', readonly=True,
        states={'draft': [('readonly', False)]}
    )