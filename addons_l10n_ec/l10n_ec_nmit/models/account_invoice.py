from functools import lru_cache
from collections import defaultdict

from odoo import api, models, fields, _, Command
from odoo.exceptions import UserError
from odoo.tools import float_round

from ..xades.sri import DocumentXML
class AccountMove(models.Model):
    _inherit = ['account.move', 'account.l10n.ec.edi']
    _name = 'account.move'

    def decimal_reports(self, number):
        return float_round(
            number, 
            precision_digits=self.env.company.currency_id.decimal_places
        )
    
    
    @property
    def _tax_group(self, tax_line_id_filter=None, tax_ids_filter=None, filter='withhold'):
        """ get report"""
        from collections import defaultdict
        self.ensure_one()
        tax_line_id_filter = tax_line_id_filter or (lambda aml, tax: True)
        tax_ids_filter = tax_ids_filter or (lambda aml, tax: True)
        balance_multiplicator = -1 if self.is_inbound() else 1
        tax_lines_data = defaultdict(lambda: defaultdict(float))
        for line in self.line_ids:
            if line.tax_line_id and tax_line_id_filter(line, line.tax_line_id) \
                    and filter not in line.tax_line_id.tax_group_id.l10n_ec_type:
                if line.tax_line_id.tax_group_id.l10n_ec_type in tax_lines_data:
                    tax_lines_data[line.tax_line_id.tax_group_id.l10n_ec_type]['amount'] += (
                        line.amount_currency * balance_multiplicator
                    )
                    continue
                tax_lines_data[line.tax_line_id.tax_group_id.l10n_ec_type].update({
                    'amount': line.amount_currency * balance_multiplicator,
                    'code': line._vat_code.get(line.tax_line_id.tax_group_id.l10n_ec_type),
                    'code_porcent': line._vat_code_porcent.get(line.tax_line_id.tax_group_id.l10n_ec_type),
                    'tarifa': line.tax_line_id.amount
                })
            if line.tax_ids:
                for base_tax in line.tax_ids.flatten_taxes_hierarchy():
                    if not tax_ids_filter(line, base_tax) \
                            or filter in base_tax.tax_group_id.l10n_ec_type: 
                        continue
                    if base_tax.tax_group_id.l10n_ec_type in tax_lines_data:
                        tax_lines_data[base_tax.tax_group_id.l10n_ec_type]['base'] += (
                            line.amount_currency * balance_multiplicator
                        )
                        continue
                    tax_lines_data[base_tax.tax_group_id.l10n_ec_type].update({
                        'base': line.amount_currency * balance_multiplicator,
                        'code': line._vat_code.get(base_tax.tax_group_id.l10n_ec_type),
                        'code_porcent': line._vat_code_porcent.get(base_tax.tax_group_id.l10n_ec_type),
                        'tarifa': base_tax.amount
                    })
        return tax_lines_data

    @lru_cache()
    def _taxes_by_group(self):
        """function help format the data for RIDE"""
        # TODO: this function have to be remove by _tax_group
        taxes_by_group = self._tax_group
        def get_value_from_dict(type_tax, type_amount):
            return self.decimal_reports(
                taxes_by_group.get(type_tax, {}).get(type_amount) or 0.00
            )
        return get_value_from_dict

    @api.returns('self', lambda value: value.id)
    def copy(self, default={}):
        default.update({
            'l10n_ec_auth_number_vendor': '',
        })
        return super(AccountMove, self).copy(default)

    @api.depends(
    'edi_document_ids',
    'edi_document_ids.state',
    'edi_document_ids.blocking_level',
    'edi_document_ids.edi_format_id',
    'edi_document_ids.edi_format_id.name')
    def _compute_edi_web_services_to_process(self):
        for move in self:
            to_process = move.edi_document_ids.filtered(
                lambda d: d.state in ('to_send', 'to_cancel') and d.blocking_level != 'error'
            )
            format_web_services = to_process.edi_format_id.filtered(lambda f: f._needs_web_services())
            if not move.l10n_latam_document_type_id.code in ('18', '07', '03', '04', '05', '42'):
                move.edi_web_services_to_process = ''
                continue
            move.edi_web_services_to_process = ', '.join(f.name for f in format_web_services)

    def action_retry_edi_documents_error(self):
        self.edi_document_ids.write({'error': False, 'blocking_level': False})
        response = DocumentXML("<?xml version='1.0' encoding='UTF-8'?>")\
                .get_auth(self.l10n_ec_access_key)
        if not response or not response.autorizaciones \
                or response.autorizaciones.autorizacion[0].estado != 'AUTORIZADO':
            return self.action_process_edi_web_services()
        self._update_document(
            response.autorizaciones.autorizacion[0], '1'
        )     
        self.edi_document_ids.filtered(
            lambda x: x.edi_format_id.code == 'xades_ec'
        ).write({
            'state': 'sent',
        })
    
    def _get_wh_edit_data(self):
        if not self.wh_id: return
        dict_error = {
            'info': 1, 'warning': 2, 'error': 3
        }
        dict_states = {
            'to_cancel': 4, 'to_send': 3, 
            'cancelled': 2, 'sent': 1
        }
        error = lambda level: dict_error.get(level, 0)
        state = lambda level: dict_states.get(level, 0)
        for move_id in self:
            vals = defaultdict(lambda: '')
            for edi_doc in move_id.edi_document_ids:
                if (
                    not edi_doc.edi_format_id._needs_web_services()
                    or not edi_doc.error
                ): continue
                vals['edi_error_count'] =+ 1
                if not error(edi_doc.blocking_level) > error(vals['edi_blocking_level']):
                    continue
                vals['edi_blocking_level'] = edi_doc.blocking_level
                vals['edi_error_message'] = edi_doc.error
                if state(edi_doc.state) > state(vals['edi_state']):
                    vals['edi_state'] = edi_doc.state
                vals['edi_web_services_to_process'] =+ edi_doc.name
            vals and move_id.wh_id.write(vals) 

    @property
    def _prepare_edocumente(self):
        edi_document_id = self.edi_document_ids.filtered(
            lambda x: x.state == 'sent'
                and x.edi_format_id.code == 'xades_ec'
        ).attachment_id
        return {
            'attachment_ids': [Command.link(edi_document_id[0].id)]
        } if edi_document_id else {}
    
    def action_send_ride(self):
        ride_template = self.env.ref('l10n_ec_nmit.invoice_ride_template')
        email_values = self._prepare_edocumente
        return ride_template.send_mail(
            self.id, force_send=True,
            email_values=email_values
        )

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        res = super()._onchange_invoice_line_ids()
        if self.move_type not in ('in_invoice', 'out_invoice'):
            return res
        for line in self.line_ids:
            if line.exclude_from_invoice_tab: continue
            for tax in line.tax_ids:
                if tax.tax_group_id.l10n_ec_type != 'withhold_income_tax': continue
                tag_ids = tax.invoice_repartition_line_ids.filtered(
                    lambda rl: rl.repartition_type == 'base'
                ).tag_ids.ids
                if not tag_ids: continue
                line.tax_tag_ids =[( 6, 0, line.tax_tag_ids.ids + tag_ids)]
        return res
    
    def action_process_edi_web_services(self):  
        if self.l10n_latam_document_type_id.code == '03':  
            return super(AccountMove, self.with_context(edi_template='l10n_ec_nmit.liq_purchase')).action_process_edi_web_services()
        return super().action_process_edi_web_services()

    def _is_manual_document_number(self):
        return self.journal_id.type == 'purchase' and self.l10n_latam_document_type_id.internal_type != 'purchase_liquidation'

    def _get_ec_payment_formatted_sequence(self, number=0):
        return f"{self.journal_id.code}/{self.payment_type == 'inbound' and 'IN' or 'OUT' }/" \
                f"{self.date.year}/{self.date.month}/{number:0<9}"

    def _get_starting_sequence(self):
        if self.payment_type:
            return self._get_ec_payment_formatted_sequence()
        return super()._get_starting_sequence()
    
    def _set_next_sequence(self):
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        new2 = not last_sequence
        if new2:
            last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()
        format, format_values = self._get_sequence_format_param(last_sequence)
        if new2:
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

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.payment_type:
            where_string += """
            AND payment_type = %(payment_type)s
            """
            param["payment_type"] = self.payment_type or ''
        if self.country_code == "EC" and self.l10n_latam_document_type_id:
            where_string += """
            AND l10n_latam_document_type_id = %(l10n_latam_document_type_unique_id)s
            """
            param["l10n_latam_document_type_unique_id"] = self.l10n_latam_document_type_id.id
            if self.journal_id.type == 'purchase' and self.l10n_latam_document_type_id.internal_type == 'purchase_liquidation'\
                    and self.l10n_latam_document_type_id.id not in param.get('l10n_latam_document_type_id'):
                param['l10n_latam_document_type_id'] = param['l10n_latam_document_type_id'] + (self.l10n_latam_document_type_id.id,)
        return where_string, param
    
    @api.depends(
        'partner_id', 'company_id', 'invoice_date',
        'l10n_latam_document_type_id',
        'journal_id', 'l10n_latam_document_number',
    )
    def _compute_l10n_ec_access_key(self):
        return super(AccountMove, self)._compute_l10n_ec_access_key()

    def _automatic_wh(self):
        return self.move_type in (self.env['ir.default'].sudo().get(
            'res.config.settings', 'wh_automatic'
        ) or '')

    def _l10n_ec_need_wh(self):
        need_wh_type_code = lambda move_type, codes: self.move_type == move_type \
            and self.l10n_latam_document_type_id.code in codes \
            and self.date <= fields.Date.today()
        if not self._automatic_wh(): return
        elif not need_wh_type_code('in_invoice', ('01', '03')) \
                and not need_wh_type_code( 'out_invoice', ('15','09', '18')):
            return        
        elif not self.mapped('invoice_line_ids.tax_ids').filtered(
                    lambda x: x.tax_group_id.l10n_ec_type in (
                        'withhold_vat', 'withhold_income_tax'
                    )
                ):
            return
        return True
        

    def action_create_wh(self):
        account_move = self.env['account.move']
        for inv in self:
            if not inv._l10n_ec_need_wh(): continue
            wh = self.env["account.wh"].create({
                "partner_id": inv.partner_id.id,
                "move_ids": [(6, 0, inv.ids)],
                "move_type": inv.move_type,
                "date": inv.date,
                "journal_id": inv.journal_id.id
            })
            wh._onchange_move_id()
            wh._compute_l10n_latam_document_type()
            if inv.move_type == 'out_invoice': continue
            account_move |= wh.action_validate()
        return account_move

    @property
    def _reconcile_wh(self):
        for move_id in self:
            account_id  = move_id.wh_id.move_type == "in_invoice" \
                and move_id.partner_id.property_account_payable_id \
                or move_id.partner_id.property_account_receivable_id
            _gt_account = lambda x: x.account_id == account_id
            (
                move_id.wh_id.move_ids.mapped('line_ids').filtered(_gt_account) 
                + move_id.line_ids.filtered(_gt_account)
            ).reconcile()
    
    @property
    def l10n_ec_total_discount(self):
        total_discount = 0.00
        for line in self.invoice_line_ids:
            total_discount= total_discount + float(line.l10n_ec_discount)
        return f'{total_discount:.2f}'

    def _set_edi(self):
        edi_document_vals_list = []
        for move in self:
            for edi_format in move.journal_id.edi_format_ids:
                if not edi_format._is_required_for_invoice(move): continue
                existing_edi_document = move.edi_document_ids.filtered(
                    lambda x: x.edi_format_id == edi_format
                )
                if existing_edi_document:
                    existing_edi_document.write({
                        'state': 'to_send',
                        'attachment_id': False,
                    })
                else:
                    edi_document_vals_list.append({
                        'edi_format_id': edi_format.id,
                        'move_id': move.id,
                        'wh_id':move.wh_id.id,
                        'state': 'to_send',
                    })
        if not edi_document_vals_list: return
        self.env['account.edi.document'].create(edi_document_vals_list)
        # self.env.ref('account_edi.ir_cron_edi_network')._trigger()

    def _post(self, soft=True):
        posted = super(AccountMove, self)._post(soft=soft)
        self.action_create_wh()
        return posted

    def action_annull(self):
        self.write({ 'state': 'annull'})

    def action_restore(self):
        self.write({'state': 'posted'})

    @api.model_create_multi
    def create(self, list_values):
        for i in list_values:
            reversed_id = self.browse(i.get('reversed_entry_id'))
            i['l10n_ec_invoice_origin'] = reversed_id.name and reversed_id.name[len(reversed_id.name)-17:len(reversed_id.name)]
            i['l10n_ec_invoice_origin_date'] = reversed_id.invoice_date
        return super(AccountMove, self).create(list_values)

    #Permite registrar una factura de proveedor del exterior, permite seleccionar tipo de documento 16 DAU
    def _get_l10n_ec_identification_type(self):
        res = super(AccountMove, self)._get_l10n_ec_identification_type()
        self.ensure_one()
        move = self
        it_ruc = self.env.ref("l10n_ec.ec_ruc", False)        
        it_passport = self.env.ref("l10n_ec.ec_passport", False)
        is_ruc = move.partner_id.commercial_partner_id.l10n_latam_identification_type_id.id == it_ruc.id
        is_passport = move.partner_id.commercial_partner_id.l10n_latam_identification_type_id.id == it_passport.id
        l10n_ec_is_importation = move.partner_id.commercial_partner_id.country_id.code != 'EC'
        identification_code = False
        if move.move_type in ("in_invoice", "in_refund"):
            if l10n_ec_is_importation:
                if is_ruc:
                    identification_code = "20"
                elif is_passport:
                    identification_code = "21"
                else:
                    identification_code = "09"
                return identification_code
            else:
                return res
        else:
            return res

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        if self.journal_id.company_id.account_fiscal_country_id != self.env.ref('base.ec') or not \
                self.journal_id.l10n_latam_use_documents:
            return super()._get_l10n_latam_documents_domain()
        domain = [
            ('country_id.code', '=', 'EC'),
            ('internal_type', 'in', ['invoice', 'purchase_liquidation', 'debit_note', 'credit_note', 'invoice_in'])
        ]
        internal_type = self._get_l10n_ec_internal_type()
        internal_type2 = self.env.context.get("internal_type", "purchase_liquidation")
        allowed_documents = self._get_l10n_ec_documents_allowed(self._get_l10n_ec_identification_type())
        identification_num = self._get_l10n_ec_identification_type()
        if identification_num and identification_num in ('09','20','21'):
            allowed_documents |= self.env.ref('l10n_ec_nmit.ec_dt_00', False)
        if internal_type and allowed_documents:
            if identification_num == "02":
                domain.append(("id", "in", allowed_documents.filtered(lambda x: (x.internal_type == internal_type or x.internal_type == internal_type2)).ids))
            else:
                domain.append(("id", "in", allowed_documents.filtered(lambda x: x.internal_type == internal_type).ids))
        return domain

    @api.constrains('l10n_ec_auth_number_vendor')
    def check_auth_number_vendor(self):
        """
        Metodo que verifica la longitud de la autorizacion
        10: documento fisico
        35: factura electronica modo online
        49: factura electronica modo offline
        """
        for s in self:
            if s.move_type not in ['in_invoice','in_refund']:
                return
            if s.l10n_ec_auth_number_vendor and len(s.l10n_ec_auth_number_vendor) not in [10, 35, 49]:
                #raise UserError(_("You must enter 10, 35 or 49 digits depending on the document."))
                raise UserError(_("El número de autorización debe ser de 10, 35 o 49 dígitos dependiendo del tipo de documento."))

    wh_ids = fields.Many2many(
        "account.wh", 'move_wh_rel', 'move_id', 'wh_id',
        "Relational document", required=False,
        states={"draft": [("readonly", False)]}, copy=False,
    )
    wh_id = fields.Many2one('account.wh')
    state = fields.Selection(selection_add=[
        ('annull', 'Annull'),
    ], ondelete={'annull': 'cascade'})

    l10n_ec_invoice_origin = fields.Char(string='Source Invoice')
    l10n_ec_invoice_origin_date = fields.Date(string='Source Invoice Date')

    tax_support_mapping_id = fields.Many2one(
        comodel_name='l10n.ec.tax.support.mapping',
        string='tax support',#Sustento tributario
    )

    l10n_ec_sri_payment_id = fields.Many2one(
        comodel_name='l10n_ec.sri.payment',
        string='Payment Method',#Mètodo de pago
    )
    tag_ids =  fields.Many2many(
        comodel_name = 'account.tag',
        string='Tag'
    )
    l10n_ec_auth_number_vendor = fields.Char(string='Authoritation number', copy=False)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive')
    ], string='Payment Type')
