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
