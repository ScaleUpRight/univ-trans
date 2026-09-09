"""Make Freight Mode editable on every quotation template.

x_studio_freight_mode used to be `related='opportunity_id.x_studio_freight_mode'`,
so editing it on a quotation wrote straight back to the opportunity. The Studio
sale.order form therefore locked it behind
`readonly="not is_opportunity_fields_editable"` (True only for the 'Quote Art' and
'Quote Commercial' templates).

The field is now quotation-owned (the opportunity only seeds it), so the gate is
obsolete: two quotations off one opportunity are meant to hold different modes.

The field is placed on the form by `studio_customization` -- an *imported* module
with no files on disk, which loads after this one -- so a view xpath in this module
cannot target it. Patch the Studio view's arch instead. Nothing reloads that module
from disk, so the change is durable. Idempotent.
"""

import json
import logging

from lxml import etree

_logger = logging.getLogger(__name__)

FIELD = "x_studio_freight_mode"
DROP_ATTRS = ("readonly", "force_save")


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT id FROM ir_ui_view
         WHERE model = 'sale.order' AND type = 'form'
           AND arch_db::text LIKE %s
        """,
        ["%%%s%%" % FIELD],
    )
    view_ids = [row[0] for row in cr.fetchall()]
    if not view_ids:
        _logger.warning("No sale.order form view carries %s; nothing to unlock.", FIELD)
        return

    for view_id in view_ids:
        cr.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", [view_id])
        arch_by_lang = cr.fetchone()[0] or {}
        changed = False

        for lang, arch in list(arch_by_lang.items()):
            if not arch or FIELD not in arch:
                continue
            root = etree.fromstring(arch.encode())
            touched = False
            for node in root.iter("field"):
                if node.get("name") != FIELD:
                    continue
                for attr in DROP_ATTRS:
                    if node.get(attr) is not None:
                        del node.attrib[attr]
                        touched = True
            if touched:
                arch_by_lang[lang] = etree.tostring(root, encoding="unicode")
                changed = True

        if changed:
            cr.execute(
                "UPDATE ir_ui_view SET arch_db = %s::jsonb WHERE id = %s",
                [json.dumps(arch_by_lang), view_id],
            )
            _logger.info("Unlocked %s on sale.order form view %s.", FIELD, view_id)
