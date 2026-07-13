from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_ops_region = fields.Selection([
        ('israel', 'Israel'),
        ('international', 'International'),
    ], string='Operations Region')

    x_ops_task_count = fields.Integer(
        string='Ops Jobs',
        compute='_compute_x_ops_task_count',
    )

    @api.depends('name')
    def _compute_x_ops_task_count(self):
        for order in self:
            order.x_ops_task_count = self.env['project.task'].search_count([
                ('x_sale_order_id', '=', order.id),
            ])

    def action_open_ops_tasks(self):
        self.ensure_one()
        tasks = self.env['project.task'].search([('x_sale_order_id', '=', self.id)])
        if len(tasks) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'view_mode': 'form',
                'res_id': tasks.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('x_sale_order_id', '=', self.id)],
            'name': 'Ops Jobs',
        }

    def action_confirm(self):
        result = super().action_confirm()
        for order in self:
            order._create_ops_calendar_task()
        return result

    def _create_ops_calendar_task(self):
        self.ensure_one()

        if not self.x_ops_region:
            return

        if self.x_ops_region == 'israel':
            project = self.env.ref(
                'univ_trans_ops_calendar.project_israel_ops',
                raise_if_not_found=False,
            )
        else:
            project = self.env.ref(
                'univ_trans_ops_calendar.project_international',
                raise_if_not_found=False,
            )

        if not project:
            return

        # Prevent duplicate task if SO is confirmed more than once
        existing = self.env['project.task'].search([
            ('x_sale_order_id', '=', self.id),
        ], limit=1)
        if existing:
            return

        planned_stage = self.env.ref(
            'univ_trans_ops_calendar.stage_planned',
            raise_if_not_found=False,
        )

        task = self.env['project.task'].create({
            'name': f'[{self.name}] {self.partner_id.name}',
            'project_id': project.id,
            'partner_id': self.partner_id.id,
            'stage_id': planned_stage.id if planned_stage else False,
            'x_sale_order_id': self.id,
            'x_opportunity_id': self.opportunity_id.id if self.opportunity_id else False,
            'x_region': self.x_ops_region,
            'x_service_address': self.partner_shipping_id.contact_address if self.partner_shipping_id else '',
        })

        # Auto-subscribe dispatch group members as followers
        dispatch_group = self.env.ref(
            'univ_trans_ops_calendar.group_ops_dispatch',
            raise_if_not_found=False,
        )
        if dispatch_group:
            dispatch_users = self.env['res.users'].sudo().search([
                ('group_ids', 'in', dispatch_group.ids),
            ])
            if dispatch_users:
                task.message_subscribe(
                    partner_ids=dispatch_users.mapped('partner_id').ids
                )

        return task
