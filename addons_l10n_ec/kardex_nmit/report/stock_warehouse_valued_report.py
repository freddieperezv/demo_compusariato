from odoo import api, fields, models, tools


class StockWarehouseValuedReport(models.Model):
    _name = "stock.warehouse.valued.report"
    _description = "Stock Warehouse Value Report"
    _auto = False
    _rec_name = "move_id"
    _order = "warehouse_id ASC, date ASC"

    move_id = fields.Many2one(comodel_name="stock.move", string="Stock Move", readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", readonly=True)
    date = fields.Datetime(string="Move Date", readonly=True)
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Stock Picking", readonly=True)
    picking_type_id = fields.Many2one(comodel_name="stock.picking.type", string="Stock Picking Type", readonly=True)
    purchase_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order", readonly=True)
    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", readonly=True)
    # inventory_id = fields.Many2one(comodel_name="stock.inventory", string="Stock Inventory", readonly=True)
    scrap_id = fields.Many2one(comodel_name="stock.scrap", string="Stock Scrap", readonly=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product Variant", readonly=True)
    product_tmpl_id = fields.Many2one(comodel_name="product.template", string="Product Template", readonly=True)
    categ_id = fields.Many2one(comodel_name="product.category", string="Category", readonly=True)
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse", readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", readonly=True)
    partner_country_id = fields.Many2one(comodel_name="res.country", string="Country", readonly=True)
    uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", readonly=True)
    product_qty = fields.Float(string="Quantity", readonly=True, digits="Product Unit of Measure")
    price_unit = fields.Float(
        string="Price Unit",
        readonly=True,
        group_operator="avg",
        digits="Price Unit"
    )
    value = fields.Float(string="Value", readonly=True, digits="Account")
    move_type = fields.Selection(
        string="Move Direction",
        selection=[
            ("input", "Input"),
            ("output", "Output"),
        ],
        readonly=True,
    )
    transaction_type = fields.Selection(
        string="Transaction Type",
        selection=[
            ("purchase", "Purchase"),
            ("sales", "Sales"),
            ("inventory_adjust", "Inventory Adjust"),
            ("scrap", "Scrap"),
            ("transfer", "Transfer"),
        ],
        readonly=True,
    )
    partner_type = fields.Selection(
        string="Partner Type",
        selection=[
            ("national", "National"),
            ("foreign", "Foreign"),
        ],
        readonly=True,
    )

    @api.model
    def hook_transaction_type(self):
        return ""

    @api.model
    def _select(self):
        return """
            SELECT
                sm.id,
                sm.id as move_id,
                sm.date,
                sm.picking_id,
                po.id as purchase_id,
                so.id as sale_order_id,
                sm.product_id,
                spt.id as picking_type_id,
                pt.id as product_tmpl_id,
                pc.id as categ_id,
                pt.uom_id,
                ss.id as scrap_id,
                rc.id AS company_id,
                case
                    when po.id is not null then
                        prpc.id
                    when so.id is not null then
                        srpc.id
                    else
                        rpcc.id
                end AS partner_id,
                rp.country_id AS partner_country_id,
                CASE
                    when po.id is not null and prpc.country_id = rpc.country_id then
                        'national'
                    when po.id is not null and prpc.country_id != rpc.country_id then
                        'foreign'
                    when so.id is not null and srpc.country_id = rpc.country_id then
                        'national'
                    when so.id is not null and srpc.country_id != rpc.country_id then
                        'foreign'
                    when rpcc.country_id = rpc.country_id then
                        'national'
                    when rpcc.country_id != rpc.country_id then
                        'foreign'
                    ELSE
                        'foreign'
                END AS partner_type,
                case
                    when slo.usage = 'internal' then
                        sm.product_qty * -1
                    when sld.usage = 'internal' then
                        sm.product_qty
                end as product_qty,
                case
                    when slo.usage = 'internal' then
                        r1.warehouse_id
                    when sld.usage = 'internal' then
                        r2.warehouse_id
                end as warehouse_id,
                case
                    when slo.usage = 'internal' then
                        'output'
                    when sld.usage = 'internal' then
                        'input'
                end as move_type,
                case
                when po.id is not null then
                    'purchase'
                when so.id is not null then
                    'sales'
                when ss.id is not null then
                    'scrap'
                """ + self.hook_transaction_type() + """
                else
                    'transfer'
                end as transaction_type,
                (r3.value / sm.product_qty) as price_unit,
                r3.value
        """

    @api.model
    def _from(self):
        return """
                from stock_move as sm
                left join (
                    select svl.stock_move_id, sum(value) as value
                    from stock_valuation_layer svl
                    group by (svl.stock_move_id)
                ) as r3 on r3.stock_move_id = sm.id
                inner join stock_location slo on slo.id = sm.location_id
                inner join stock_location sld on sld.id = sm.location_dest_id
                inner join product_product as pp on pp.id = sm.product_id
                inner join product_template as pt on pt.id = pp.product_tmpl_id
                inner join product_category as pc on pc.id = pt.categ_id
                left join (
                    select sl.id, t.id as warehouse_id
                    from
                    stock_location as sl,
                    (
                        select sw.id, sl.parent_path
                        from stock_warehouse sw
                        left join stock_location sl on sl.id = sw.view_location_id
                    ) as t
                    where sl.parent_path like (t.parent_path || '%')
                ) as r1 on r1.id = sm.location_id
                left join (
                    select sl.id, t.id as warehouse_id
                    from
                    stock_location as sl,
                    (
                        select sw.id, sl.parent_path
                        from stock_warehouse sw
                        left join stock_location sl on sl.id = sw.view_location_id
                    ) as t
                    where sl.parent_path like (t.parent_path || '%')
                ) as r2 on r2.id = sm.location_dest_id
                left join purchase_order_line pol on pol.id = sm.purchase_line_id
                left join purchase_order as po on po.id = pol.order_id
                left join sale_order_line sol on sol.id = sm.sale_line_id
                left join sale_order as so on so.id = sol.order_id
                left join stock_scrap as ss on ss.move_id = sm.id
                left join stock_picking as sp on sp.id = sm.picking_id
                left join stock_picking_type as spt on spt.id = sp.picking_type_id
                LEFT JOIN res_partner rp ON rp.id = sm.partner_id
                LEFT JOIN res_partner rpcc ON rpcc.id = rp.commercial_partner_id
                LEFT JOIN res_partner srp ON srp.id = so.partner_id
                LEFT JOIN res_partner prp ON prp.id = po.partner_id
                LEFT JOIN res_partner srpc ON srpc.id = srp.commercial_partner_id
                LEFT JOIN res_partner prpc ON prpc.id = prp.commercial_partner_id
                LEFT JOIN res_company rc ON rc.id = sm.company_id
                LEFT JOIN res_partner rpc ON rpc.id = rc.partner_id
        """

    @api.model
    def _where(self):
        return """
        where
            sm.state = 'done'
            and pt.type = 'product'
            and sm.product_qty > 0
            and r3.value is not null
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(  # pylint: disable=E8103
            """
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s
            )
        """
            % (self._table, self._select(), self._from(), self._where())
        )

    def get_document_number(self):
        self.ensure_one()
        doc_number = self.move_id.picking_id.display_name
        if self.purchase_id:
            doc_number = self.purchase_id.display_name
        elif self.sale_order_id:
            doc_number = self.sale_order_id.display_name
        # elif self.inventory_id:
        #     doc_number = self.inventory_id.display_name
        elif self.scrap_id:
            doc_number = self.scrap_id.display_name
        return doc_number
