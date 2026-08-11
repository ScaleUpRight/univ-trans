from lxml import etree
from markupsafe import Markup

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import format_amount, format_date, format_datetime, replace_exceptions

from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.sale.controllers.portal import CustomerPortal

ORDER_VIEWER_GROUP = 'univ_trans_portal_customisation.group_order_viewer'

# Bookkeeping and mail plumbing: present on every model, meaningless on a read-only page.
LEAD_FIELD_BLOCKLIST = frozenset({
    'id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date',
    '__last_update', 'access_token', 'access_url', 'access_warning',
    'meeting_display_date', 'meeting_display_label',
})
LEAD_FIELD_PREFIX_BLOCKLIST = (
    'message_', 'activity_', 'my_activity', 'website_message', 'rating_', 'has_message',
)
# Structural nodes that carry actions rather than data.
LEAD_SKIP_TAGS = frozenset({'header', 'button', 'chatter', 'templates', 'kanban', 'searchpanel'})


class CustomerPortal(CustomerPortal):

    def _is_order_viewer(self):
        return request.env.user.has_group(ORDER_VIEWER_GROUP)

    # ------------------------------------------------------------------
    # Sales orders
    # ------------------------------------------------------------------

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

        return self._serve_folder_document(order_sudo, document_id)

    # ------------------------------------------------------------------
    # Opportunities
    # ------------------------------------------------------------------

    def _prepare_opportunities_domain(self):
        return [('type', '=', 'opportunity')]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'opportunity_count' in counters:
            values['opportunity_count'] = (
                request.env['crm.lead'].search_count(self._prepare_opportunities_domain())
                if self._is_order_viewer() else 0
            )
        return values

    @http.route(
        ['/my/opportunities', '/my/opportunities/page/<int:page>'],
        type='http', auth='user', website=True,
    )
    def portal_my_opportunities(self, page=1, sortby=None, **kw):
        if not self._is_order_viewer():
            raise request.not_found()

        Lead = request.env['crm.lead']
        domain = self._prepare_opportunities_domain()
        searchbar_sortings = {
            'date': {'label': _("Newest"), 'order': 'create_date desc'},
            'name': {'label': _("Name"), 'order': 'name'},
            'stage': {'label': _("Stage"), 'order': 'stage_id'},
        }
        if sortby not in searchbar_sortings:
            sortby = 'date'

        pager_values = portal_pager(
            url='/my/opportunities',
            total=Lead.search_count(domain),
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby},
        )
        leads = Lead.search(
            domain,
            order=searchbar_sortings[sortby]['order'],
            limit=self._items_per_page,
            offset=pager_values['offset'],
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'opportunities': leads.sudo(),
            # the shared breadcrumb template tests `lead` on both pages
            'lead': False,
            'page_name': 'opportunity',
            'pager': pager_values,
            'default_url': '/my/opportunities',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('univ_trans_portal_customisation.portal_my_opportunities', values)

    @http.route('/my/opportunities/<int:lead_id>', type='http', auth='user', website=True)
    def portal_opportunity_page(self, lead_id, **kw):
        if not self._is_order_viewer():
            raise request.not_found()

        lead_sudo = self._check_lead_access(lead_id)
        if lead_sudo is None:
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()
        values.update({
            'lead': lead_sudo,
            'sections': self._lead_portal_sections(lead_sudo),
            'documents': lead_sudo.documents_file_ids.filtered(lambda d: d.type == 'binary'),
            'page_name': 'opportunity',
        })
        return request.render('univ_trans_portal_customisation.portal_opportunity_page', values)

    @http.route(
        '/my/opportunities/<int:lead_id>/document/<int:document_id>',
        type='http', auth='user', website=True,
    )
    def portal_opportunity_document(self, lead_id, document_id, **kw):
        if not self._is_order_viewer():
            raise request.not_found()

        lead_sudo = self._check_lead_access(lead_id)
        if lead_sudo is None:
            return request.redirect('/my')

        return self._serve_folder_document(lead_sudo, document_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_lead_access(self, lead_id):
        """Return the lead as sudo if the current user may read it, else None.

        Deliberately not `_document_check_access`: that falls back to comparing an
        `access_token`, which crm.lead does not carry, so the fallback path would
        raise AttributeError instead of AccessError.  Here the record rule is the
        only thing that decides.
        """
        lead = request.env['crm.lead'].browse(lead_id)
        try:
            lead.check_access('read')
        except (AccessError, MissingError):
            return None
        lead_sudo = lead.sudo().exists()
        return lead_sudo or None

    def _serve_folder_document(self, record_sudo, document_id):
        """Stream a document belonging to `record_sudo`'s own Documents folder."""
        document_sudo = record_sudo.documents_file_ids.filtered(lambda d: d.id == document_id)
        if not document_sudo or document_sudo.type != 'binary' or not document_sudo.attachment_id:
            raise request.not_found()

        with replace_exceptions(ValueError, MissingError, by=request.not_found()):
            stream = request.env['ir.binary']._get_stream_from(document_sudo)
        return stream.get_response(as_attachment=True)

    # -- dynamic field rendering ---------------------------------------

    def _lead_field_blocked(self, name, info):
        if name in LEAD_FIELD_BLOCKLIST or name.startswith(LEAD_FIELD_PREFIX_BLOCKLIST):
            return True
        return info.get('type') == 'binary'

    def _lead_field_value(self, lead_sudo, name, info):
        """Format one field for display.  Returns None to skip the field entirely.

        Done in Python rather than with `t-field` because the template renders a
        field list that is only known at runtime, and `t-field` needs a literal
        field name.
        """
        ftype = info.get('type')
        try:
            value = lead_sudo[name]
        except Exception:
            return None

        if ftype == 'boolean':
            return _("Yes") if value else _("No")
        if ftype == 'monetary':
            currency = lead_sudo.company_currency or request.env.company.currency_id
            return format_amount(request.env, value or 0.0, currency)
        if ftype in ('integer', 'float'):
            return value
        if not value:
            return ''
        if ftype == 'many2one':
            return value.sudo().display_name or ''
        if ftype in ('one2many', 'many2many'):
            return ', '.join(n for n in value.sudo().mapped('display_name') if n)
        if ftype == 'selection':
            return dict(info.get('selection') or []).get(value, value)
        if ftype == 'date':
            return format_date(request.env, value)
        if ftype == 'datetime':
            return format_datetime(request.env, value)
        if ftype == 'html':
            return Markup(value)
        return value

    def _lead_walk_arch(self, node, sections, current, seen):
        for child in node:
            if not isinstance(child.tag, str) or child.tag in LEAD_SKIP_TAGS:
                continue
            # Only skip statically hidden nodes; a conditional `invisible` domain is
            # left in, since evaluating it here would mean reimplementing the client.
            if child.get('invisible') in ('1', 'True', 'true'):
                continue

            if child.tag == 'field':
                name = child.get('name')
                if name and name not in seen:
                    seen.add(name)
                    current['fields'].append((name, child.get('string')))
            elif child.tag in ('page', 'group') and child.get('string'):
                section = {'title': child.get('string'), 'fields': []}
                sections.append(section)
                self._lead_walk_arch(child, sections, section, seen)
            else:
                self._lead_walk_arch(child, sections, current, seen)

    def _lead_portal_sections(self, lead_sudo):
        """Build [(section title, [(label, value), ...]), ...] for the detail page.

        The field list and its order come from the *combined* form arch returned by
        `get_view()`, so anything added later through Studio shows up here with the
        label and position it was given, without touching this module.  Whatever the
        form does not mention is then swept up into a trailing section, so "all
        fields" stays literally true rather than "all fields someone put on a form".
        """
        finfos = lead_sudo.fields_get()
        sections, seen = [], set()
        root_section = {'title': '', 'fields': []}
        sections.append(root_section)

        try:
            arch = etree.fromstring(lead_sudo.get_view(view_type='form')['arch'])
            self._lead_walk_arch(arch, sections, root_section, seen)
        except Exception:
            # A broken or unusual form view must not take the page down; the
            # sweep-up pass below still renders every field.
            sections, seen = [root_section], set()

        rendered = []
        for section in sections:
            rows = []
            for name, label in section['fields']:
                info = finfos.get(name)
                if not info or self._lead_field_blocked(name, info):
                    continue
                value = self._lead_field_value(lead_sudo, name, info)
                if value is None:
                    continue
                rows.append((label or info.get('string') or name, value))
            if rows:
                rendered.append((section['title'], rows))

        extra = []
        for name, info in sorted(finfos.items(), key=lambda kv: (kv[1].get('string') or kv[0])):
            if name in seen or not info.get('store') or self._lead_field_blocked(name, info):
                continue
            value = self._lead_field_value(lead_sudo, name, info)
            if value is None or value == '':
                continue
            extra.append((info.get('string') or name, value))
        if extra:
            rendered.append((_("Other"), extra))

        return rendered
