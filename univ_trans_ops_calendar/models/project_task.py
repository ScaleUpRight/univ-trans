from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='set null',
        index=True,
    )
    x_opportunity_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        ondelete='set null',
        index=True,
    )
    x_job_number = fields.Char(
        string='Job Number',
        related='x_opportunity_id.opportunity_file_id',
        store=True,
        readonly=True,
    )
    x_service_address = fields.Char(string='Service Address')
    x_region = fields.Selection([
        ('israel', 'Israel'),
        ('international', 'International'),
    ], string='Region')
    x_notes = fields.Text(string='Operational Notes')

    def write(self, vals):
        result = super().write(vals)
        if 'stage_id' in vals:
            confirmed_stage = self.env.ref(
                'univ_trans_ops_calendar.stage_confirmed',
                raise_if_not_found=False,
            )
            if confirmed_stage and vals['stage_id'] == confirmed_stage.id:
                template = self.env.ref(
                    'univ_trans_ops_calendar.email_template_job_confirmed',
                    raise_if_not_found=False,
                )
                if template:
                    for task in self:
                        if task.partner_id and task.partner_id.email:
                            template.sudo().send_mail(task.id, force_send=False)
        return result

    def unlink(self):
        if not self.env.user.has_group('project.group_project_manager'):
            raise UserError(_('Only project managers can delete jobs.'))
        return super().unlink()
