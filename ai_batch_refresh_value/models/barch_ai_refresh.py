from odoo import models, fields, api

class BatchAIRefresh(models.Model):

    _name = 'batch.ai.refresh'
    _description = 'Batch AI Refresh'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    refresh_ai_fields_ids = fields.One2many('batch.ai.refresh.line', 'batch_ai_refresh_id')


class BatchAIRefreshLines(models.Model):

    _name = 'batch.ai.refresh.line'

    field_id = fields.Many2one('ir.model.fields', string='Fields', required=True, ondelete='cascade')
    batch_ai_refresh_id = fields.Many2one('batch.ai.refresh')
