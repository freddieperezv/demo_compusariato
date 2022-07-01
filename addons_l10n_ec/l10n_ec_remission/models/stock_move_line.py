from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"


    def generate_remission_lines(self):
        """Generate values for the remision lines"""
        for i in self:
            line_params = [
				('company_id', '=', self.env.user.company_id.id),
				('product_id', '=', i.product_id.id),
				('guide_line_id.picking_id', '=', i.picking_id.id),
				('product_uom_id', '=', i.product_uom_id.id)
			]
            i.lot_id and line_params.append(('lot_id', '=', i.lot_id.id))
            line_amount = sum(
                self.env['account.remission.guide.stock.line'].search(
                    line_params
                ).mapped('qty_done')
            ) or 0
            yield (
				0, 0, {
				'company_id': self.env.user.company_id.id,
				'product_id': i.product_id.id,
				'product_uom_id': i.product_uom_id.id,
				'product_uom_category_id': i.product_uom_category_id.id,
				'lot_id': i.lot_id.id,
				'qty_done': i.qty_done - line_amount
			})
