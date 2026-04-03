import requests
from odoo import api, fields, models
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    opportunity_file_id = fields.Char(
        string="Opportunity File ID",
        readonly=True,
        copy=False,
        index=True,
    )

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

    x_v18_opportunity_id = fields.Integer("V18 Opportunity ID", readonly=True)

    _sql_constraints = [
        (
            "unique_opportunity_file_id",
            "unique(opportunity_file_id)",
            "Opportunity File ID must be unique.",
        )
    ]

    def action_open_documents(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': self.documents_folder_id.access_url,
            'target': 'new',
        }

    def _compute_documents_file_ids(self):
        Documents = self.env["documents.document"]
        for lead in self:
            if lead.documents_folder_id:
                lead.documents_file_ids = Documents.search([
                    ("folder_id", "=", lead.documents_folder_id.id),
                    ("type", "=", "binary"),
                ])
            else:
                lead.documents_file_ids = False

    def _prepare_opportunity_quotation_context(self):
        ctx = super()._prepare_opportunity_quotation_context()

        if self.documents_folder_id:
            ctx["default_documents_folder_id"] = self.documents_folder_id.id

        return ctx

    def create_documents_folder(self):
        document = self.env["documents.document"]

        # Find or create root "Opportunities" folder
        root = document.search([
            ("type", "=", "folder"),
            ("name", "=", "Opportunities")
        ], limit=1)

        if not root:
            root = document.create({
                "name": "Opportunities",
                "type": "folder",
            })

        for opp in self:
            if opp.documents_folder_id:
                continue

            if not opp.opportunity_file_id:
                opp.opportunity_file_id = self.env["ir.sequence"].next_by_code(
                    "crm.lead.opportunity.file"
                ) or "/"

            folder = document.create({
                "name": opp.opportunity_file_id,
                "type": "folder",
                "folder_id": root.id,
                "res_model": "crm.lead",
                "res_id": opp.id,
                "alias_name": opp.opportunity_file_id,
            })

            opp.documents_folder_id = folder.id

    def _send_to_external_api(self):
        url = "https://univers-transit-dashboard.vercel.app/api/trigger-call"

        headers = {
            "Content-Type": "application/json"
        }

        for lead in self:
            name = lead.contact_name or lead.x_studio_full_name_from_lead or lead.partner_id.name or lead.name
            env_mode = request.env['ir.config_parameter'].sudo().get_param('lead_webhook.env', 'test')

            payload = {
                "name": name if env_mode == 'prod' else "Test",
                "phone_number": lead.x_studio_phone_from_lead,
                "email": lead.x_studio_email_from_lead ,
                "origin": lead.x_studio_moving_from_city,
                "destination": lead.x_studio_move_to_city ,
                "odoo_lead_id": lead.id if lead.type == 'lead' else False,
                "opportunity_file_id": lead.id if lead.type == 'opportunity' else False
            }
            _logger.info(f"Voice AI API payload: {payload}")
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=5)
                _logger.info(f"API Response for Lead {lead.id}: {response.status_code} - {response.text}")
            except Exception as e:
                _logger.error(f"API Call Failed for Lead {lead.id}: {str(e)}")

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads.create_documents_folder()
        leads._send_to_external_api()
        return leads
