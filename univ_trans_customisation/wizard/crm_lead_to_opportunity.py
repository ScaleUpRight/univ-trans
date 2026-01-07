# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class CrmLead2opportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def _create_documents_folder(self, opportunity):
        Documents = self.env["documents.document"]

        # Find or create root "Opportunities" folder
        root = Documents.search([
            ("type", "=", "folder"),
            ("name", "=", "Opportunities")
        ], limit=1)

        if not root:
            root = Documents.create({
                "name": "Opportunities",
                "type": "folder",
            })

        for opp in opportunity:
            if opp.documents_folder_id:
                continue

            if not opp.opportunity_file_id:
                continue

            folder = Documents.create({
                "name": opp.opportunity_file_id,
                "type": "folder",
                "folder_id": root.id,
                "res_model": "crm.lead",
                "res_id": opp.id,
            })

            opp.documents_folder_id = folder.id

    def action_apply(self):
        if self.name == 'merge':
            result_opportunity = self._action_merge()
        else:
            result_opportunity = self._action_convert()
            result_opportunity.opportunity_file_id = self.env["ir.sequence"].next_by_code(
                "crm.lead.opportunity.file"
            ) or "/"
            self._create_documents_folder(result_opportunity)

        return result_opportunity.redirect_lead_opportunity_view()
