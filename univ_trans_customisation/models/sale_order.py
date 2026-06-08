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

    is_opportunity_fields_editable = fields.Boolean(
        compute="_compute_is_opportunity_fields_editable", store=True
    )

    # Templates on which the shipment/opportunity fields (size, scope, countries,
    # cities, booker type, ...) may be edited directly on the quote and on which
    # the totals block is printed on the PDF.
    # 2026-06-08: added 'Quote HHG' per client request (Ilan, WhatsApp 2026-05-25)
    # so HHG quotes are editable just like Art/Commercial.
    EDITABLE_QUOTE_TEMPLATES = ['Quote Art', 'Quote Commercial', 'Quote HHG']

    @api.depends('sale_order_template_id')
    def _compute_is_opportunity_fields_editable(self):
        for order in self:
            order.is_opportunity_fields_editable = bool(
                order.sale_order_template_id
                and order.sale_order_template_id.name in self.EDITABLE_QUOTE_TEMPLATES
            )

    x_studio_booker_type = fields.Selection(related='opportunity_id.x_studio_booker_type', readonly=False, store=True)
    x_studio_service_scope = fields.Selection(related='opportunity_id.x_studio_service_scope', readonly=False, store=True)
    x_studio_freight_mode = fields.Selection(related='opportunity_id.x_studio_freight_mode', readonly=False, store=True)
    x_studio_size = fields.Selection(related='opportunity_id.x_studio_size', readonly=False, store=True)
    x_studio_destination = fields.Boolean(compute='_compute_x_studio_destination', store=True, string="Destination")
    x_studio_freight = fields.Boolean(compute='_compute_x_studio_freight', store=True, string="Freight")
    x_studio_origin = fields.Boolean(compute='_compute_x_studio_origin', store=True, string="Origin")
    x_studio_shipment_direction = fields.Char(compute='_compute_x_studio_shipment_direction', readonly=False, store=True)
    x_studio_moving_from_country = fields.Char(compute='_compute_x_studio_moving_from_country', readonly=False, store=True)
    x_studio_moving_from_street_1 = fields.Char(compute='_compute_x_studio_moving_from_street_1', store=True)
    x_studio_move_to_country = fields.Char(compute='_compute_x_studio_move_to_country', readonly=False, store=True)
    # 2026-06-08: per-quote ORIGIN/DESTINATION CITY (Ilan, WhatsApp 2026-03-24).
    # Same pattern as the *_country fields above: defaults from the opportunity but
    # can be overridden on the quote and is stored independently per quote.
    x_studio_moving_from_city = fields.Char(compute='_compute_x_studio_moving_from_city', readonly=False, store=True)
    x_studio_move_to_city = fields.Char(compute='_compute_x_studio_move_to_city', readonly=False, store=True)

    @api.depends('x_studio_service_scope', 'opportunity_id.x_studio_destination')
    def _compute_x_studio_destination(self):
        for order in self:
            if order.opportunity_id.x_studio_destination:
                order.x_studio_destination = order.opportunity_id.x_studio_destination
            else:
                scope = order.x_studio_service_scope
                order.x_studio_destination = scope in (
                    'door_to_door',
                    'port_to_door',
                )

    @api.depends('x_studio_service_scope', 'opportunity_id.x_studio_freight')
    def _compute_x_studio_freight(self):
        for order in self:
            if order.opportunity_id.x_studio_freight:
                order.x_studio_freight = order.opportunity_id.x_studio_freight
            else:
                scope = order.x_studio_service_scope
                order.x_studio_freight = scope in (
                    'door_to_door',
                    'door_to_port_destination',
                    'port_to_door',
                    'port_to_port',
                )

    @api.depends('x_studio_service_scope', 'opportunity_id.x_studio_origin')
    def _compute_x_studio_origin(self):
        for order in self:
            if order.opportunity_id.x_studio_origin:
                order.x_studio_origin = order.opportunity_id.x_studio_origin
            else:
                scope = order.x_studio_service_scope
                order.x_studio_origin = scope in (
                    'door_to_door',
                    'door_to_port_destination',
                    'door_to_port_origin',
                )

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

    @api.depends('opportunity_id.x_studio_moving_from_city')
    def _compute_x_studio_moving_from_city(self):
        for order in self:
            order.x_studio_moving_from_city = order.opportunity_id.x_studio_moving_from_city

    @api.depends('opportunity_id.x_studio_move_to_city')
    def _compute_x_studio_move_to_city(self):
        for order in self:
            order.x_studio_move_to_city = order.opportunity_id.x_studio_move_to_city

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

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id_quotes(self):
        if self.sale_order_template_id:
            # 1. Grab all IDs from the template (Headers AND Footers)
            template_docs = self.sale_order_template_id.quotation_document_ids.ids

            if template_docs:
                # 2. Use Command.set (which is code 6) to select the whole list
                # This prevents the "only 1 selected" issue
                self.quotation_document_ids = [fields.Command.set(template_docs)]
            else:
                self.quotation_document_ids = [fields.Command.clear()]
