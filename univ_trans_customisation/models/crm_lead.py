from odoo import api, fields, models


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
            })

            opp.documents_folder_id = folder.id

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads.create_documents_folder()
        return leads
