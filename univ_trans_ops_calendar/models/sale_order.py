from datetime import timedelta

from odoo import api, fields, models

# Spellings that count as a domestic (Israel) location in the free-text
# x_studio_*_country fields. Extend here if the data uses other variants.
ISRAEL_NAMES = {'israel', 'il', 'isr', 'ישראל'}

# Per-activity generation matrix.
# Each entry: (service_type, day offset from the move date, duration in hours).
# The move date is the sale order's Delivery Date (commitment_date); see
# _ops_base_datetime() for the fallback when it is empty.
ORIGIN_ACTIVITIES = [
    ('Survey', -7, 2),
    ('Packing', -1, 8),
    ('Pickup', 0, 4),
]
# International freight leg. There is no dedicated "Freight" service type, so the
# transport booking rides under "Other" (per decision: use existing values only).
FREIGHT_ACTIVITIES = [
    ('Customs', 1, 4),
    ('Other', 2, 8),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
            order._generate_ops_activities()
        return result

    # ------------------------------------------------------------------
    # Operations calendar generation
    # ------------------------------------------------------------------
    def _get_ops_region(self):
        """Israel vs International, derived from existing quote data.

        Primary signal is the shipment direction flag: an Export/Import move is
        cross-border -> International; a Local move is domestic -> Israel. For a
        Drop move (or when the direction is blank) we fall back to the country
        fields: International if any leg sits outside Israel.
        """
        self.ensure_one()
        direction = (self.x_studio_shipment_direction or '').strip().lower()
        if direction in ('export', 'import'):
            return 'international'
        if direction == 'local':
            return 'israel'

        # Drop / blank -> look at the countries.
        countries = [
            (c or '').strip().lower()
            for c in (self.x_studio_moving_from_country, self.x_studio_move_to_country)
            if (c or '').strip()
        ]
        if not countries:
            return 'israel'  # ambiguous -> assume domestic
        if all(c in ISRAEL_NAMES for c in countries):
            return 'israel'
        return 'international'

    def _ops_activity_plan(self, region):
        """Return the ordered list of activities to open for this order.

        Driven by the scope booleans already computed on the sale order
        (x_studio_origin / x_studio_freight / x_studio_destination). Storage is
        intentionally out of scope for now.
        """
        self.ensure_one()
        plan = []
        if self.x_studio_origin:
            plan += ORIGIN_ACTIVITIES
        if self.x_studio_freight and region == 'international':
            plan += FREIGHT_ACTIVITIES
        if self.x_studio_destination:
            delivery_offset = 14 if region == 'international' else 1
            plan.append(('Delivery', delivery_offset, 4))
        return plan

    def _ops_base_datetime(self):
        """Anchor date for the activity schedule (the 'move day')."""
        self.ensure_one()
        base = self.commitment_date or self.date_order or fields.Datetime.now()
        # Work from 08:00 local start of that day.
        return base.replace(hour=8, minute=0, second=0, microsecond=0)

    def _prepare_ops_task_vals(self, service, project, stage, start, end):
        self.ensure_one()
        return {
            'name': f'[{self.name}] {service} – {self.partner_id.name}',
            'project_id': project.id,
            'partner_id': self.partner_id.id,
            'stage_id': stage.id if stage else False,
            'x_studio_service_type': service,
            'x_sale_order_id': self.id,
            'x_opportunity_id': self.opportunity_id.id if self.opportunity_id else False,
            'x_region': self._get_ops_region(),
            'x_service_address': self.partner_shipping_id.contact_address if self.partner_shipping_id else '',
            'planned_date_begin': start,
            'date_deadline': end,
        }

    def _generate_ops_activities(self):
        self.ensure_one()

        region = self._get_ops_region()
        plan = self._ops_activity_plan(region)
        if not plan:
            return  # nothing to schedule for this order

        project = self.env.ref(
            'univ_trans_ops_calendar.project_israel_ops'
            if region == 'israel'
            else 'univ_trans_ops_calendar.project_international',
            raise_if_not_found=False,
        )
        if not project:
            return

        # Prevent duplicates if the SO is confirmed more than once.
        existing = self.env['project.task'].search_count([
            ('x_sale_order_id', '=', self.id),
        ])
        if existing:
            return

        planned_stage = self.env.ref(
            'univ_trans_ops_calendar.stage_planned',
            raise_if_not_found=False,
        )
        base_dt = self._ops_base_datetime()

        tasks = self.env['project.task']
        for service, offset, duration in plan:
            start = base_dt + timedelta(days=offset)
            end = start + timedelta(hours=duration)
            tasks |= self.env['project.task'].create(
                self._prepare_ops_task_vals(service, project, planned_stage, start, end)
            )

        # Auto-subscribe dispatch group members as followers of every job.
        dispatch_group = self.env.ref(
            'univ_trans_ops_calendar.group_ops_dispatch',
            raise_if_not_found=False,
        )
        if dispatch_group:
            dispatch_users = self.env['res.users'].sudo().search([
                ('group_ids', 'in', dispatch_group.ids),
            ])
            if dispatch_users:
                tasks.message_subscribe(
                    partner_ids=dispatch_users.mapped('partner_id').ids
                )

        return tasks
