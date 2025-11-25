from odoo import models, fields, api

class BatchAIRefresh(models.Model):

    _name = 'batch.ai.refresh'
    _description = 'Batch AI Refresh'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    refresh_ai_fields_ids = fields.Many2many('ir.model.fields',  "ai_refresh_fields_rel",
        "batch_ai_refresh_id",
        "field_id",)
    refresh_ai_fields_domain = fields.Binary(compute='_compute_refresh_ai_fields')

    @api.depends('model_id')
    def _compute_refresh_ai_fields(self):
        """Update domain + clear values when model changes."""
        for record in self:
            domain = [('model_id', '=', record.model_id.id), ('ai', '=', True)]
            record.refresh_ai_fields_domain =  domain
