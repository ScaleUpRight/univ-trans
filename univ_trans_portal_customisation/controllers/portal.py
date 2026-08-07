from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import replace_exceptions

from odoo.addons.sale.controllers.portal import CustomerPortal

ORDER_VIEWER_GROUP = 'univ_trans_portal_customisation.group_order_viewer'


class CustomerPortal(CustomerPortal):

    def _is_order_viewer(self):
        return request.env.user.has_group(ORDER_VIEWER_GROUP)

    def _prepare_orders_domain(self, partner):
        """Order viewers browse every confirmed order, not only their own.

        This one override also fixes the /my portal home counter, which calls
        the same method (sale/controllers/portal.py).  `_prepare_quotations_domain`
        is deliberately left alone so /my/quotes stays personal-only.
        """
        if self._is_order_viewer():
            return [('state', '=', 'sale')]
        return super()._prepare_orders_domain(partner)

    @http.route(
        '/my/orders/<int:order_id>/document/<int:document_id>',
        type='http', auth='user', website=True,
    )
    def portal_order_document(self, order_id, document_id, access_token=None, **kw):
        """Serve a document filed under an order the current user may read.

        documents.document is guarded by a *global* record rule
        ([('user_permission', '!=', 'none')], documents/security/security.xml), and
        `user_permission` cannot be satisfied for a share user through group rules:
        `access_internal` is skipped for share users and folder inheritance only
        reaches one level.  So the document is fetched with sudo() -- but only after
        the order access check has passed and the document has been confirmed to
        belong to that order's own folder.  The order check is what grants access;
        sudo() only carries out the read.

        The viewer group is checked explicitly: the order rule added by this module
        is OR'ed with sale's stock portal rule, so an ordinary customer still passes
        `_document_check_access` on an order of their own.  Without this gate they
        could hand-craft the URL and pull files out of their order's document folder,
        which may hold internal paperwork the portal never intends to show.  404
        rather than a redirect, so the route does not confirm the id exists.
        """
        if not self._is_order_viewer():
            raise request.not_found()

        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        document_sudo = order_sudo.documents_file_ids.filtered(lambda d: d.id == document_id)
        if not document_sudo or document_sudo.type != 'binary' or not document_sudo.attachment_id:
            raise request.not_found()

        with replace_exceptions(ValueError, MissingError, by=request.not_found()):
            stream = request.env['ir.binary']._get_stream_from(document_sudo)
        return stream.get_response(as_attachment=True)
