from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    documents_folder_id = fields.Many2one(
        "documents.document",
        string="Documents Folder",
        readonly=True,
        copy=False,
    )

    documents_file_ids = fields.Many2many(
        "documents.document",
        string="Documents",
        compute="_compute_documents_file_ids",
        store=False,
    )

    x_studio_booker_type = fields.Selection(related='opportunity_id.x_studio_booker_type')
    x_studio_destination = fields.Boolean(related='opportunity_id.x_studio_destination')
    x_studio_freight = fields.Boolean(related='opportunity_id.x_studio_freight')
    x_studio_origin = fields.Boolean(related='opportunity_id.x_studio_origin')
    x_studio_service_scope = fields.Selection(related='opportunity_id.x_studio_service_scope')
    x_studio_shipment_direction = fields.Char(compute='_compute_x_studio_shipment_direction')
    x_studio_moving_from_country = fields.Char(compute='_compute_x_studio_moving_from_country')
    x_studio_moving_from_street_1 = fields.Char(compute='_compute_x_studio_moving_from_street_1')
    x_studio_move_to_country = fields.Char(compute='_compute_x_studio_move_to_country')

    @api.depends('opportunity_id.x_studio_moving_from_country')
    def _compute_x_studio_moving_from_country(self):
        for order in self:
            order.x_studio_moving_from_country = order.opportunity_id.x_studio_moving_from_country

    @api.depends('opportunity_id.x_studio_move_from_street')
    def _compute_x_studio_moving_from_street_1(self):
        for order in self:
            order.x_studio_moving_from_street_1 = order.opportunity_id.x_studio_move_from_street

    @api.depends('opportunity_id.x_studio_move_to_country')
    def _compute_x_studio_move_to_country(self):
        for order in self:
            order.x_studio_move_to_country = order.opportunity_id.x_studio_move_to_country

    @api.depends('opportunity_id.x_studio_shipment_direction')
    def _compute_x_studio_shipment_direction(self):
        for order in self:
            order.x_studio_shipment_direction = order.opportunity_id.x_studio_shipment_direction

    def _compute_documents_file_ids(self):
        Documents = self.env["documents.document"]
        for order in self:
            if order.documents_folder_id:
                order.documents_file_ids = Documents.search([
                    ("folder_id", "=", order.documents_folder_id.id),
                    ("type", "=", "binary"),
                ])
            else:
                order.documents_file_ids = False

    def action_open_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.documents_folder_id.access_url,
            'target': 'new',
        }

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.documents_folder_id:
            vals["documents_folder_id"] = self.documents_folder_id.id
        return vals
