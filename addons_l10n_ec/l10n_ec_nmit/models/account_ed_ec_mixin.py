from urllib import response
import markupsafe, re
from ..xades.sri import DocumentXML
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


_MODULO_11 = {
    'BASE': 11, 'FACTOR': 2,
    'RETORNO11': 0, 'RETORNO10': 1,
    'PESO': 2, 'MAX_WEIGHT': 7
}

def _evalMod11(modulo):
    if modulo == _MODULO_11['BASE']:
        return _MODULO_11['RETORNO11']
    elif modulo == _MODULO_11['BASE'] - 1:
        return _MODULO_11['RETORNO10']
    return modulo

def _computeMod11(dato):
    total = 0
    weight = _MODULO_11['PESO']
    for item in dato[::-1]:
        total += int(item) * weight
        weight += 1
        if weight > _MODULO_11['MAX_WEIGHT']:
            weight = _MODULO_11['PESO']
    return _evalMod11(11 - total % _MODULO_11['BASE'])


class L10nMxin(models.AbstractModel):
    _name = 'account.l10n.ec.edi'
    _description = 'l10n EC required functions'

    @api.returns('self', lambda value: value.id)
    def copy(self, default={}):
        default.update({
            'l10n_ec_auth_number_vendor': '',
            'l10n_ec_auth_number': '',
            'l10n_ec_auth_state': '',
            'l10n_ec_auth_env': '',
            'l10n_ec_auth_date': '',
            'l10n_ec_auth_sri': '',
            'l10n_ec_auth_access_key': '',
            'l10n_ec_emission_code': '',
        })
        return super(L10nMxin, self).copy(default)

    @property
    def l10n_ec_sequence(self):
        if not self.l10n_latam_document_number: return ''
        match = re.match(
            '(?:\d{3}-\d{3}-)(\d{9}$)', self.l10n_latam_document_number
        )
        return match and match.group(1) or ''

    @property
    def _l10n_ec_validate_data(self):
        errors = []
        if not self.company_id.partner_id.vat:
            errors.append(_('missing commpany Vat'))
        elif not self.company_id.l10n_ec_env:
            errors.append(_('missing SRI Enviroment'))
        elif not self.journal_id.l10n_ec_entity:
            errors.append(_('missing SRI Entity'))
        elif not self.journal_id.l10n_ec_emission:
            errors.append(_('missing Emission'))
        if errors: raise UserError(", ".join(errors))

    @property
    def l10n_ec_partner_address(self):
        f'{self.partner_id.street or ""} {self.partner_id.street2 or ""}'\
            .replace('\n', '').replace('\r\n', '').replace('&', '&amp;')

    @property
    def l10n_ec_cod_doc(self):
        code = self.l10n_latam_document_type_id.code
        return {
           '18': '01', '42': '07',
        }.get(code) or code

    def sum_tax_groups(self, *groups):
        group_ids = self.env['account.tax.group'].search([
            ('l10n_ec_type', 'in', groups),
        ]).ids
        tax_totals = self._get_tax_totals(
            self.partner_id, self._prepare_tax_lines_data_for_totals_from_invoice(),
            self.amount_total, self.amount_untaxed, self.currency_id
        )
        return '{:.2f}'.format(abs(sum(
            tax_group.get('tax_group_amount')
            for _, tax_groups in tax_totals.get('groups_by_subtotal').items()
            if 'groups_by_subtotal' in tax_totals
            for tax_group in tax_groups
            if tax_group.get('tax_group_id') in group_ids
        )))


    @property
    def l10n_latam_identification_type_name(self):
        type_id = self.partner_id.l10n_latam_identification_type_id
        it_ruc = self.env.ref("l10n_ec.ec_ruc", False)
        it_dni = self.env.ref("l10n_ec.ec_dni", False)
        it_passport = self.env.ref("l10n_ec.ec_passport", False)
        return {
            type_id == it_dni: '05',
            type_id == it_ruc: '04',
            type_id == it_passport: '06'
        }.get(True, '08')

    def _compute_l10n_ec_access_key(self):
        for inv in self:
            if (
                    not inv.l10n_latam_document_type_id.code \
                    or not inv.company_id.partner_id.vat \
                    or not inv.company_id.l10n_ec_env \
                    or not inv.journal_id.l10n_ec_entity \
                    or not inv.journal_id.l10n_ec_emission\
                    or not inv.l10n_ec_sequence
            ): continue
            values = f"""{(
                    (hasattr(inv, 'invoice_date') and inv.invoice_date)
                    or inv.date
                    or fields.Date.today()
                ).strftime("%d%m%Y")}""" \
                f'{inv.l10n_ec_cod_doc}' \
                f'{inv.company_id.partner_id.vat}' \
                f'{inv.company_id.l10n_ec_env}' \
                f'{inv.journal_id.l10n_ec_entity}' \
                f'{inv.journal_id.l10n_ec_emission}' \
                f'{inv.l10n_ec_sequence}{inv.company_id.partner_id.vat[5:13]}1'
            inv.l10n_ec_access_key = values + str(_computeMod11(values))

    def _get_l10n_ec_taxes(self):
        return self.invoice_line.taxes

    def _create_inv_att(self, xml_content, xml_name, error='', success=False):
        return {
            'attachment': self.env['ir.attachment'].create({
                'name': xml_name,
                'raw': xml_content.encode(),
                'res_model': self._name == "account.remission.guide" and self._name or 'account.move',
                'res_id': self.id,
                'mimetype': 'application/xml'
            }),
            'success': success,
            'error': error
        }

    def _update_document(self, auth, codes):
        """ Updates sent document with
        answer values from SRI """
        self.write({
            "l10n_ec_auth_number": auth.numeroAutorizacion,
            "l10n_ec_auth_state": auth.estado,
            "l10n_ec_auth_env": auth.ambiente,
            "l10n_ec_auth_date": auth.fechaAutorizacion.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            ),
            "l10n_ec_auth_sri": True,
            "l10n_ec_auth_access_key": self.l10n_ec_access_key,
            "l10n_ec_emission_code": codes
        })

    @property
    def _get_xml_name(self):
        if self.env.context.get('edi_template'):
            return self.env.context['edi_template']
        if hasattr(self, 'wh_id') and self.wh_id:
            return f'l10n_ec_nmit.{self.wh_id._table}'
        return f'l10n_ec_nmit.{self.move_type}'

    def _export_xades_ec(self):
        res = {}
        for inv in self:
            # self.check_date(self.invoice_date)
            # self.check_before_sent()
            xml_content = markupsafe.Markup(
                "<?xml version='1.0' encoding='UTF-8'?>"
            )
            xml_content += self.env.ref(self._get_xml_name
            )._render({'i': inv})
            document_type = {
                self.move_type == "in_invoice" \
                    and self.l10n_latam_document_type_id.code == "03": "liq_purchase",
                hasattr(self, 'wh_id') and self.wh_id \
                    and self.move_type == 'entry': 'withdrawing',
                self.move_type == 'entry' \
                    and self.l10n_latam_document_type_id.code == "06": 'delivery'
            }.get(True) or self.move_type
            inv_xml = DocumentXML(xml_content, document_type, inv.company_id.l10n_ec_env)
            auth = None
            signed_document = inv.company_id.action_sign(xml_content)
            try:
                error = inv_xml.validate_xml()
                if not error:
                    errors = inv_xml.send_receipt(signed_document)
                    if not errors:
                        auth, m = inv_xml.request_authorization(
                            self.l10n_ec_access_key
                        )
                        if m: error = " ".join(m)
                        elif auth.estado != 'AUTORIZADO':  error = auth.estado
                    else: error = '\n'.join(errors)
            except Exception as e:
                error = e.args
            xml_content = markupsafe.Markup(signed_document)
            xml_name = f'{inv.name.replace("/", "_")}_xades.xml'
            if error:
                res[inv] = inv._create_inv_att(
                    xml_content, xml_name, error=error
                )
                continue
            res[inv] = inv._create_inv_att(xml_content, xml_name, success=True)
            self._update_document(auth, '1')
        return res


    l10n_ec_access_key = fields.Char(
        compute='_compute_l10n_ec_access_key', store=True
    )

    l10n_ec_auth_number = fields.Char(readonly=True)
    l10n_ec_auth_state = fields.Char(readonly=True)
    l10n_ec_auth_env = fields.Char(readonly=True)
    l10n_ec_auth_date = fields.Char(readonly=True)
    l10n_ec_auth_sri = fields.Char(readonly=True)
    l10n_ec_auth_access_key = fields.Char(readonly=True)
    l10n_ec_emission_code = fields.Char(readonly=True)