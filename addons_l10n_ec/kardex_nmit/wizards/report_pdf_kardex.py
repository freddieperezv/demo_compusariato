from datetime import timedelta
from functools import lru_cache
import logging
from odoo.tools.float_utils import float_round, float_is_zero
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

from odoo import fields, models, api


class ReportKardexPDF(models.AbstractModel):
    _name = 'stock.kardex.wizard.pdf'
    _description = 'PDF kardex report'

    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse"
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product"
    )
    date_to = fields.Datetime(
        string="Date To"
                              )
    date_from = fields.Datetime(
        string="Date From"
    )
    lot_id = fields.Many2many(
        comodel_name='stock.production.lot',
        string="Lote/Serie",
        domain="[('product_id', '=', product_id)]"
    )

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_name_selection(obj, field, value):
        return dict(obj._fields[field].selection
                    ).get(value)

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_scrap_warehouse(move_id):
        return move_id.move_id.warehouse_id.name

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_scrap_name(move_id):
        return move_id.name

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_picking_name(move_id):
        return move_id.reference

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_location_name(location):
        return location.display_name

    def _get_positions(self):
        return (
            'date',
            'move_type',
            'transaction_type',
            'picking_type_id',
            'doc_number',
            'lot_id',
            'partner_id',
            'warehouse_id',
            'location_id',
            'location_dest_id',
            'input_product_qty',
            'input_unit_cost',
            'input_value',
            'output_product_qty',
            'output_unit_cost',
            'output_value',
            'balance_product_qty',
            'balance_unit_cost',
            'balance_value',
        )        

    def get_warehouses(self):
        return self.warehouse_id or self.env['stock.warehouse'].search([])

    def _get_quantity_product(self):
        stock_layer = self.env['stock.valuation.layer'].search([
            ('create_date', '<', self.date_from), ('product_id', '=', self.product_id.id)
        ])
        return sum([i.value for i in stock_layer])

    def get_data_report(self, warehouse):
        valuation_report_model = self.env['stock.warehouse.valued.report']
        search_criteria = []
        if self.product_id:
            search_criteria.append(('product_id', '=', self.product_id.id))
        search_criteria.append(('date', '<=', self.date_to))
        search_criteria.append(('date', '>=', self.date_from))
        search_criteria.append(('warehouse_id', '=', warehouse.id))
        if self.lot_id:
            search_criteria.append(('move_id.move_line_ids.lot_id', 'in', self.lot_id.ids))
        reports = valuation_report_model.search(search_criteria, order="date")
        return reports

    def _get_locations(self, warehouse):
        location_model = self.env['stock.location']
        warehouse_locations = location_model.search([
            ('location_id', 'child_of', warehouse.view_location_id.id),
            ('usage', '=', 'internal')
        ])
        return warehouse_locations

    def _get_qty_available(self, product=False, lot=False, to_date=False):
        lote, date_to = self._context.get('lot_id'), self._context.get('to_date')
        if lot:
            lote = lot.id
        if to_date:
            date_to = to_date
        if not product:
            product = self.product_id
        product_qty = product._compute_quantities_dict(
            lote, self._context.get('owner_id'),
            self._context.get('package_id'), self._context.get('from_date'),
            date_to
        )
        return product_qty[product.id]['qty_available']

    def get_initial_data(self, product, warehouse):
        valuation_report_model = self.env['stock.warehouse.valued.report']
        last_qty_available, current_value, unit_cost = 0, 0, 0
        grouped_data = valuation_report_model.read_group([
            ('product_id', '=', product.id),
            ('date', '<=', self.date_from - timedelta(seconds=1)),
            ('warehouse_id', '=', warehouse.id)
        ], ['product_id', 'product_qty', 'value'], ['product_id'])
        if grouped_data:
            last_qty_available = grouped_data[0]['product_qty']
            current_value = grouped_data[0]['value']
            unit_cost = last_qty_available != 0 and (current_value / last_qty_available) or 0
        return last_qty_available, current_value, unit_cost

    @lru_cache(maxsize=None)
    def get_uom_precision(self):
        return self.env['decimal.precision'].precision_get('Product Unit of Measure')

    @lru_cache(maxsize=None)
    def get_cost_precision(self):
        return self.env['decimal.precision'].precision_get('Price Unit')

    @lru_cache(maxsize=None)
    def get_account_precision(self):
        return self.env['decimal.precision'].precision_get('Account')
