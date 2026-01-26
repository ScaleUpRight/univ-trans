from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    x_studio_shipment_direction_line = fields.Char(compute='_compute_x_studio_shipment_direction')

    @api.depends('order_id.x_studio_shipment_direction')
    def _compute_x_studio_shipment_direction(self):
        for line in self:
            line.x_studio_shipment_direction_line = line.order_id.x_studio_shipment_direction
