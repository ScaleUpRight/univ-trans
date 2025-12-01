from odoo import models, _, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):

    _inherit = 'crm.lead'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('website'):
                vals['website'] = self.env['res.partner']._clean_website(vals['website'])
        ctx = dict(self.env.context)
        ctx.update({'mail_create_nolog': True})
        self = self.with_context(ctx)
        leads = super().create(vals_list)

        if self.default_get(['partner_id']).get('partner_id') is None:
            commercial_partner_ids = [vals['commercial_partner_id'] for vals in vals_list if vals.get('commercial_partner_id')]
            CommercialPartners = self.env['res.partner'].with_prefetch(commercial_partner_ids)
            for lead, lead_vals in zip(leads, vals_list, strict=True):
                if not lead_vals.get('partner_id') and lead_vals.get('commercial_partner_id'):
                    commercial_partner = CommercialPartners.browse(lead_vals['commercial_partner_id'])
                    if (lead.phone or lead.email_from) and (
                        lead.phone_sanitized != commercial_partner.phone_sanitized or
                        lead.email_normalized != commercial_partner.email_normalized
                    ):
                        lead.partner_name = lead.partner_name or commercial_partner.name
                        continue
                    lead.partner_id = commercial_partner

        leads._handle_won_lost({}, {
            lead.id: {
                'is_lost': lead.won_status == 'lost',
                'is_won': lead.won_status == 'won',
            } for lead in leads
        })

        return leads

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
                if not record[field.field_id.name]:
                    try:
                        result = record.get_ai_field_value(field.field_id.name, {})
                        record[field.field_id.name] = result
                        self.env.cr.commit()
                    except Exception as e:
                        # Log error but continue processing remaining fields
                        _logger.error(
                            "AI refresh failed for field '%s' on record %s: %s",
                            field.field_id.name, record.id, e
                        )
                        continue
