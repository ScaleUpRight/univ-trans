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

    _sql_constraints = [
        (
            "unique_opportunity_file_id",
            "unique(opportunity_file_id)",
            "Opportunity File ID must be unique.",
        )
    ]

    # def _create_documents_folder(self):
    #     Documents = self.env["documents.document"]
    #
    #     # Find or create root "Opportunities" folder
    #     root = Documents.search([
    #         ("type", "=", "folder"),
    #         ("name", "=", "Opportunities")
    #     ], limit=1)
    #
    #     if not root:
    #         root = Documents.create({
    #             "name": "Opportunities",
    #             "type": "folder",
    #         })
    #
    #     for lead in self:
    #         if lead.documents_folder_id:
    #             continue
    #
    #         if not lead.opportunity_file_id:
    #             continue
    #
    #         folder = Documents.create({
    #             "name": lead.opportunity_file_id,
    #             "type": "folder",
    #             "folder_id": root.id,
    #             "res_model": "crm.lead",
    #             "res_id": lead.id,
    #         })
    #
    #         lead.documents_folder_id = folder.id
    #
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if not vals.get("opportunity_file_id"):
    #             vals["opportunity_file_id"] = self.env["ir.sequence"].next_by_code(
    #                 "crm.lead.opportunity.file"
    #             ) or "/"
    #     records = super().create(vals_list)
    #     for record in records:
    #         record._create_documents_folder()
    #     return records
