from odoo import models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):

    _inherit = 'crm.lead'

    def batch_ai_refresh_fields(self):
        crm_lead_ai_config = self.env['batch.ai.refresh'].search([('model_id.model', '=', 'crm.lead')])
        if crm_lead_ai_config:
            for record in self:
                for field in crm_lead_ai_config.refresh_ai_fields_ids:
                    if not record[field.name]:
                        record[field.name] = record.get_ai_field_value(field.name, {})
        else:
            raise UserError(_(
                "No AI configuration found for CRM Lead. "
                "Please set it up under AI → Configuration → Batch AI Refresh."
            ))
