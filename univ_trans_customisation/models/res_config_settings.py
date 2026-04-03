from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_voice_integration_env = fields.Selection(
        [
            ('test', 'Test'),
            ('prod', 'Production')
        ],
        string="Webhook Environment",
        default='test',
        config_parameter='lead_webhook.env'
    )
