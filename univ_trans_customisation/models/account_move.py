from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

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

    def _compute_documents_file_ids(self):
        Documents = self.env["documents.document"]
        for move in self:
            if move.documents_folder_id:
                move.documents_file_ids = Documents.search([
                    ("folder_id", "=", move.documents_folder_id.id),
                    ("type", "=", "binary"),
                ])
            else:
                move.documents_file_ids = False

    def action_open_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.documents_folder_id.access_url,
            'target': 'new',
        }
