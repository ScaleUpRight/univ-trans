from odoo import models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):

    _inherit = 'crm.lead'

    def batch_ai_refresh_fields(self):
        crm_lead_ai_config = self.env['batch.ai.refresh'].search([
            ('model_id.model', '=', 'crm.lead')
        ])

        if not crm_lead_ai_config:
            raise UserError(_(
                "No AI configuration found for CRM Lead. "
                "Please set it up under AI → Configuration → Batch AI Refresh."
            ))

        for record in self:
            for field in crm_lead_ai_config.refresh_ai_fields_ids:
                if not record[field.name]:
                    try:
                        result = record.get_ai_field_value(field.name, {})
                        record[field.name] = result
                    except Exception as e:
                        # Log error but continue processing remaining fields
                        _logger.error(
                            "AI refresh failed for field '%s' on record %s: %s",
                            field.name, record.id, e
                        )
                        continue

