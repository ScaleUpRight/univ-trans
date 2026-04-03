import re
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LeadWebhookController(http.Controller):

    @http.route('/api/webhook/lead-update', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def lead_update(self, **kwargs):
        try:
            data = request.get_json_data()

            _logger.info("Webhook Received: %s", data)

            lead_id = data.get('odoo_lead_id') or data.get('opportunity_file_id')
            if not lead_id:
                return {"success": False, "message": "Missing odoo_lead_id"}

            lead = request.env['crm.lead'].sudo().browse(lead_id)

            if not lead.exists():
                return {"success": False, "message": "Lead not found"}

            update_vals = {}

            # ---- Move Description ----
            if data.get('x_studio_move_size_description'):
                update_vals['x_studio_move_size_description'] = data.get('x_studio_move_size_description')

            # ---- Route Fields ----
            route = data.get('route', {})

            # ---- Move Date (no conversion) ----
            if route.get('x_studio_move_date'):
                update_vals['x_studio_move_date'] = route.get('x_studio_move_date')

            # ---- FROM ADDRESS ----
            from_addr = route.get('x_studio_move_from_street')
            if from_addr:
                parsed = self.parse_address(from_addr)

                update_vals['x_studio_move_from_street'] = from_addr

                if parsed.get('city'):
                    update_vals['x_studio_moving_from_city'] = parsed['city']

                if parsed.get('zip'):
                    update_vals['x_studio_moving_from_postal_code'] = parsed['zip']

            # ---- TO ADDRESS ----
            to_addr = route.get('x_studio_move_to_street')
            if to_addr:
                parsed = self.parse_address(to_addr)

                update_vals['x_studio_move_to_street'] = to_addr

                if parsed.get('city'):
                    update_vals['x_studio_move_to_city'] = parsed['city']

                if parsed.get('zip'):
                    update_vals['x_studio_moving_to_postal_code'] = parsed['zip']

            # ---- Write ----
            if update_vals:
                lead.sudo().write(update_vals)

            _logger.info(f"Lead {lead_id} updated with {update_vals}")

            return {
                "success": True,
                "message": "Lead updated successfully"
            }

        except Exception as e:
            _logger.exception("Webhook Error")
            return {
                "success": False,
                "message": str(e)
            }

    # -----------------------------
    # Simple Address Parser
    # -----------------------------
    def parse_address(self, full_address):
        """
        Expected format:
        Street, ZIP City
        Example:
        70 Downing Street, 747487 Singapore
        """
        result = {
            "street": full_address,
            "zip": False,
            "city": False,
        }

        try:
            parts = full_address.split(',')
            if len(parts) >= 2:
                street = parts[0].strip()
                rest = parts[1].strip()

                match = re.match(r'(\d+)\s+(.*)', rest)
                if match:
                    result["zip"] = match.group(1)
                    result["city"] = match.group(2)

                result["street"] = street

        except Exception:
            pass

        return result