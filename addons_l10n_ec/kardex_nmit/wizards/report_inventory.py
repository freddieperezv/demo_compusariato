# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
from io import BytesIO
import xlsxwriter
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from functools import lru_cache
from odoo.tools.float_utils import float_round, float_is_zero


_logger = logging.getLogger(__name__)


class ReportKardexWizard(models.TransientModel):
    _name = "stock.kardex.wizard"
    _inherit = ['stock.kardex.wizard.pdf']

    LETTERS = list(map(chr, range(65, 90)))

    @api.model
    def toDigits(self, n, b):
        """Convert a positive number n to its digit representation in base b."""
        digits = []
        if n == 0:
            digits.append(0)
        while n > 0:
            digits.insert(0, n % b)
            n = n // b
        return digits

    @api.model
    def GetLetterForPosition(self, position):
        numbers = self.toDigits(position, (len(self.LETTERS) - 1))
        pos = [self.LETTERS[n] for n in numbers]
        return "".join(pos)

    report = fields.Selection([
        ('pdf', 'PDF'),
        ('xls', 'Excel'),
    ], default='xls')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)


    @api.model
    def default_get(self, field):
        rec = super(ReportKardexWizard, self).default_get(field)
        rec['date_to'] = datetime.now()
        rec['date_from'] = datetime.now() - timedelta(days=30)
        return rec

    def action_report_pdf_kardex(self):
        return self.env.ref('kardex_nmit.action_report_kardex_pdf').report_action(self)

    def generate_report(self):
        if self.report == 'pdf':
            return self.action_report_pdf_kardex()
        else:
            return self.action_report_xlsx_kardex()

    def xslx_body(self, workbook, name):
        bold = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'align': 'center', 'bold': True, 'border': 1})
        format_title.set_center_across()
        format_title.set_align('vjustify')
        format_title_b = workbook.add_format({'align': 'center', 'bold': False, 'border': 1})
        format_title_b.set_center_across()
        format_title_b.set_text_wrap()
        format_title_b.set_align('vjustify')
        format_title_1 = workbook.add_format({'align': 'center', 'bold': True, 'border': 1})

        format_title2 = workbook.add_format({'align': 'left', 'bold': True})
        format_title7 = workbook.add_format({'align': 'left', 'bold': True, 'border': 1})
        format_title6 = workbook.add_format({'align': 'left'})
        format_title7.set_text_wrap()
        format_title7.set_align('vjustify')
        text_format = workbook.add_format({'align': 'left', 'bold': False, 'border': 1})
        text_format.set_align('vjustify')
        format_title_num_bold = workbook.add_format({'align': 'left', 'bold': False, 'border': 1})
        format_title_num_bold.set_align('vjustify')
        format_title_num_bold.set_num_format("0.00")
        date_format = workbook.add_format({'align': 'left', 'bold': False,
                                                 'border': 1, 'num_format': 'dd/mm/yyyy hh:mm:ss'})
        date_format.set_align("vjustify")
        format_title_date_n = workbook.add_format(
            {'align': 'left', 'bold': False, 'num_format': 'dd/mm/yyyy hh:mm:ss'})
        format_title_date_n.set_align("vjustify")
        numeric_format = workbook.add_format({'align': 'right', 'bold': False, 'border': 1})
        numeric_format.set_num_format("#,##0.00")
        format_title3 = workbook.add_format({'align': 'left', 'bold': True, 'border': 1})
        format_title4 = workbook.add_format({'align': 'left', 'bold': True})
        format_title3.set_bg_color("#b9b7b7")
        cost_format = workbook.add_format({'align': 'right', 'bold': False, 'border': 1})
        price_unit_precision = self.env['decimal.precision'].search([
            ('name', '=', 'Price Unit'),
        ])
        price_unit_format = "#,##0."
        for i in range(price_unit_precision.digits or 2):
            price_unit_format += "0"
        cost_format.set_num_format(price_unit_format)
        format_num_cost_bold = workbook.add_format({'align': 'right', 'bold': False})
        uom_precision = self.env['decimal.precision'].search([
            ('name', '=', 'Product Unit of Measure'),
        ])
        uom_format = "#,##0."
        for i in range(uom_precision.digits or 2):
            uom_format += "0"
        format_num_cost_bold.set_num_format(uom_format)

        sheet = workbook.add_worksheet(name)
        sheet.set_column(0, 5, 25)
        sheet.set_column(6, 16, 20)

        warehouses = self.get_warehouses()
        row_position = 1
        for warehouse in warehouses:
            sheet.write(row_position, 0, _('Warehouse'), format_title4)
            sheet.write(row_position, 1, warehouse.display_name or "", format_title6)
            row_position += 1
            sheet.write(row_position, 0, _('Product'), format_title4)
            sheet.write(row_position, 1, self.product_id.display_name or "", format_title6)
            row_position += 1
            sheet.write(row_position, 0, _('Date From'), format_title4)
            sheet.write(row_position, 1, self.date_from, format_title_date_n)
            row_position += 1
            sheet.write(row_position, 0, _('Date To'), format_title4)
            sheet.write(row_position, 1, self.date_to, format_title_date_n)
            row_position += 1
            sheet.write(row_position, 0, _('Company'), format_title4)
            sheet.write(row_position, 1, self.env.company.name or "", format_title6)
            row_position += 1
            sheet.write(row_position, 0, _('Valuation'), format_title4)
            sheet.write(row_position, 1, _(self._get_name_selection(self.product_id.categ_id, 'property_cost_method',
                                                         self.product_id.categ_id.property_cost_method)), format_title6)
            row_position += 2
            POSITIONS = self._get_positions()
            sheet.write(row_position, POSITIONS.index('date'), _('Date'), format_title7)
            sheet.write(row_position, POSITIONS.index('move_type'), _('Direction'), format_title7)
            sheet.write(row_position, POSITIONS.index('transaction_type'), _('Transaction Type'), format_title7)
            sheet.write(row_position, POSITIONS.index('picking_type_id'), _('Operation Name'), format_title7)
            sheet.write(row_position, POSITIONS.index('doc_number'), _('Document Number'), format_title7)
            sheet.write(row_position, POSITIONS.index('lot_id'), _('Lot'), format_title7)
            sheet.write(row_position, POSITIONS.index('partner_id'), _('Partner'), format_title7)
            sheet.write(row_position, POSITIONS.index('warehouse_id'), _('Warehouse'), format_title7)
            sheet.write(row_position, POSITIONS.index('location_id'), _('Origin Location'), format_title7)
            sheet.write(row_position, POSITIONS.index('location_dest_id'), _('Destination Location'), format_title7)
            sheet.merge_range('{1}{0}:{2}{0}'.format(
                row_position,
                self.GetLetterForPosition(POSITIONS.index('input_product_qty')),
                self.GetLetterForPosition(POSITIONS.index('input_value'))
            ), _('Incoming'), format_title7)
            sheet.write(row_position, POSITIONS.index('input_product_qty'), _('Quantity'), format_title7)
            sheet.write(row_position, POSITIONS.index('input_unit_cost'), _('Cost unit'), format_title7)
            sheet.write(row_position, POSITIONS.index('input_value'), _('Cost Total'), format_title7)
            sheet.merge_range('{1}{0}:{2}{0}'.format(
                row_position,
                self.GetLetterForPosition(POSITIONS.index('output_product_qty')),
                self.GetLetterForPosition(POSITIONS.index('output_value'))
            ), _('Outgoing'), format_title7)
            sheet.write(row_position, POSITIONS.index('output_product_qty'), _('Quantity'), format_title7)
            sheet.write(row_position, POSITIONS.index('output_unit_cost'), _('Cost unit'), format_title7)
            sheet.write(row_position, POSITIONS.index('output_value'), _('Cost Total'), format_title7)
            sheet.merge_range('{1}{0}:{2}{0}'.format(
                row_position,
                self.GetLetterForPosition(POSITIONS.index('balance_product_qty')),
                self.GetLetterForPosition(POSITIONS.index('balance_value')),
            ), _('Balance'), format_title7)
            sheet.write(row_position, POSITIONS.index('balance_product_qty'), _('Quantity'), format_title7)
            sheet.write(row_position, POSITIONS.index('balance_unit_cost'), _('Cost unit'), format_title7)
            sheet.write(row_position, POSITIONS.index('balance_value'), _('Cost Total'), format_title7)
            self.hook_header_row_write(sheet, row_position, format_title7)

            row_position += 1
            reports = self.get_data_report(warehouse)
            last_qty_available = None
            current_value = 0
            unit_cost, row_position, last_qty_available, current_value = self.write_sheet(
                self.env['stock.warehouse.valued.report'],
                text_format,
                date_format,
                numeric_format,
                cost_format,
                row_position,
                sheet,
                current_value,
                warehouse,
                last_qty_available,
                True
            )
            row_position += 1
            for report in reports:
                unit_cost, row_position, last_qty_available, current_value = self.write_sheet(
                    report,
                    text_format,
                    date_format,
                    numeric_format,
                    cost_format,
                    row_position,
                    sheet,
                    current_value,
                    warehouse,
                    last_qty_available,
                    False
                )
                row_position += 1
            row_position += 2
            for location in self._get_locations(warehouse):
                qty_available = self._get_qty_available(
                    product=self.product_id.with_context({
                        'location': location.id,
                    }), lot=self.lot_id,
                    to_date=self.date_to,
                )
                sheet.write(row_position, 0, location.display_name, format_title4)
                sheet.write(row_position, 1, qty_available, format_num_cost_bold)
                row_position += 1
            row_position += 2

    def hook_header_row_write(self, sheet, row_position, format_header):
        return True

    # def _hook_row_write(self, report,
    #                 text_format,
    #                 date_format,
    #                 numeric_format,
    #                 cost_format,
    #                 row_position,
    #                 sheet,
    #                 current_value,
    #                 warehouse,
    #                 last_qty_available=None):
    #     return True

    def write_sheet(self,
                    report,
                    text_format,
                    date_format,
                    numeric_format,
                    cost_format,
                    row_position,
                    sheet,
                    current_value,
                    warehouse,
                    last_qty_available=None,
                    is_initial=None
                    ):
        unit_cost = report.price_unit
        product_qty = report.product_qty
        POSITIONS = self._get_positions()
        if not is_initial:
            doc_number = report.get_document_number()
            sheet.write(row_position, POSITIONS.index('date'), report.date, date_format)
            sheet.write(row_position, POSITIONS.index('move_type'), self._get_name_selection(report, 'move_type', report.move_type), text_format)
            sheet.write(row_position, POSITIONS.index('transaction_type'), self._get_name_selection(report, 'transaction_type', report.transaction_type), text_format)
            sheet.write(row_position, POSITIONS.index('picking_type_id'), report.picking_type_id.display_name, text_format)
            sheet.write(row_position, POSITIONS.index('doc_number'), doc_number, text_format)
            sheet.write(row_position, POSITIONS.index('lot_id'), ' / '.join(report.move_id.mapped(
                'move_line_ids.lot_id.name')), text_format)
            sheet.write(row_position, POSITIONS.index('partner_id'), report.partner_id.display_name or "", text_format)
            sheet.write(row_position, POSITIONS.index('warehouse_id'), report.warehouse_id.display_name or "", text_format)
            sheet.write(row_position, POSITIONS.index('location_id'), report.move_id.location_id.name, text_format)
            sheet.write(row_position, POSITIONS.index('location_dest_id'), report.move_id.location_dest_id.name, text_format)
            sheet.write(row_position, POSITIONS.index('input_product_qty'), report.move_type == 'input' and product_qty or 0.0, numeric_format)
            if self.env.user.has_group('kardex_nmit.group_show_cost_kardex'):
                sheet.write(row_position, POSITIONS.index('input_unit_cost'), report.move_type == 'input' and unit_cost or 0.0, numeric_format)
                sheet.write(row_position, POSITIONS.index('input_value'), report.move_type == 'input' and product_qty * unit_cost or 0.0, cost_format)
            else:
                sheet.write(row_position, POSITIONS.index('input_unit_cost'), "", numeric_format)
                sheet.write(row_position, POSITIONS.index('input_value'), "", cost_format)
            sheet.write(row_position, POSITIONS.index('output_product_qty'), report.move_type == 'output' and product_qty or 0.0, numeric_format)
            if self.env.user.has_group('kardex_nmit.group_show_cost_kardex'):
                sheet.write(row_position, POSITIONS.index('output_unit_cost'), report.move_type == 'output' and unit_cost or 0.0, cost_format)
                sheet.write(row_position, POSITIONS.index('output_value'), report.move_type == 'output' and product_qty * unit_cost or 0.0, numeric_format)
            else:
                sheet.write(row_position, POSITIONS.index('output_unit_cost'), "", numeric_format)
                sheet.write(row_position, POSITIONS.index('output_value'), "", cost_format)
            last_qty_available += product_qty
            current_value += report.value
        else:
            last_qty_available, current_value, unit_cost = self.get_initial_data(self.product_id, warehouse)
        sheet.write(row_position, POSITIONS.index('balance_product_qty'), last_qty_available, numeric_format)
        if self.env.user.has_group('kardex_nmit.group_show_cost_kardex'):
            cost_product = 0
            if self.product_id.categ_id.property_cost_method == "average":
                if last_qty_available > 0:
                    cost_product = current_value / last_qty_available
            else:
                cost_product = unit_cost
            # sheet.write(row_position, POSITIONS.index('balance_unit_cost'), unit_cost, numeric_format) cambios fperez para presentar el costo promedio
            sheet.write(row_position, POSITIONS.index('balance_unit_cost'), cost_product, numeric_format)
            sheet.write(row_position, POSITIONS.index('balance_value'), current_value, numeric_format)
        else:
            sheet.write(row_position, POSITIONS.index('balance_unit_cost'), "", numeric_format)
            sheet.write(row_position, POSITIONS.index('balance_value'), "", numeric_format)
        # self._hook_row_write(report,
        #             text_format,
        #             date_format,
        #             numeric_format,
        #             cost_format,
        #             row_position,
        #             sheet,
        #             current_value,
        #             warehouse,
        #             last_qty_available)
        return unit_cost, row_position, last_qty_available, current_value

    def action_report_xlsx_kardex(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {'remove_timezone': True})
        name = 'Reporte de Kardex'
        self.xslx_body(workbook, name)
        workbook.close()
        file_data.seek(0)
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': name + ".xlsx",
            'store_fname': name + ".xlsx",
            'type': 'binary',
        })

        url = "/web/content/%s?download=true" % (attachment.id)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    @staticmethod
    @lru_cache(maxsize=None)
    def product_name(product_id):
        return product_id.display_name
