# Univers Transit — Change Log, 2026-06-08

Scope: the "green" quick-win items approved by Ilan/Leon from the WhatsApp audit.
Environment: **staging only** (`univ-trans-jun7-33189298`). Nothing applied to production.
Branch: `fix/green-staging-jun8` (off `Jun7`).

Legend: ✅ done (in this branch) · ⏳ awaiting deploy to staging · 🟡 awaiting your approval before I apply.

---

## A2 — Allow editing shipment/opportunity details on the **HHG** quote template ✅⏳
**Asked by:** Ilan, WhatsApp 2026-05-25 ("allow to change the details of the quote, size, volume, etc in HHG Template as well").

**Before:** The quote fields (size, service scope, countries, booker type, …) and the PDF
totals block were editable/printed **only** for templates `Quote Art` and `Quote Commercial`.
On a **Quote HHG** these fields were read-only, so the size/volume could not be changed on the quote.

**After:** `Quote HHG` is added to the editable-templates list, so HHG quotes behave exactly like
Art/Commercial — the shipment fields become editable and the totals print on the PDF.

**Changed:** `models/sale_order.py` → new constant `EDITABLE_QUOTE_TEMPLATES =
['Quote Art', 'Quote Commercial', 'Quote HHG']` used by `_compute_is_opportunity_fields_editable`.
(Also fixed a latent typo on the field: `strore=True` → `store=True`.)

**How to verify (after deploy):** open a quote that uses **Quote HHG** → the Moving From/To Country,
Size, Booker Type, etc. are now editable; print the PDF → the totals block appears.

---

## A3 — Origin/Destination **city** editable per quote (not pulled from the opportunity) ✅⏳
**Asked by:** Ilan, WhatsApp 2026-03-24 ("…and again the address, origin city and country …
shipment details should be set in the quote itself, not taken from the opportunity").

**Before:** Country was already overridable on the quote, but the **city** was always read from the
opportunity (`doc.opportunity_id.x_studio_moving_from_city` / `…move_to_city`). A second quote on the
same opportunity could not carry a different city.

**After:** Two new quote-level fields — `x_studio_moving_from_city` and `x_studio_move_to_city` — that
**default from the opportunity but can be overridden per quote** (same proven pattern as the existing
`*_country` fields). They appear on the quote form next to the country fields and are used by the PDF.

**Changed:**
- `models/sale_order.py` → two new computed-stored, user-writable Char fields + their `@api.depends`
  compute methods.
- `report/sale_order.xml` → Origin/Destination now read `doc.x_studio_moving_from_city` /
  `doc.x_studio_move_to_city` instead of the opportunity's city.
- `views/sale_order_view.xml` → new view `view_sale_order_form_inherit_city` (priority 200) places the
  two city fields after the matching country fields; editable on the same templates as A2.

**How to verify (after deploy):** on a quote, change *Moving From City*; the PDF shows the new city; a
second quote on the same opportunity can have a different city without touching the opportunity.

---

## Drift fix — Proposal Date + Expiration folded into the module report ✅⏳
**Why:** The live quote report (Studio view 3862) had **Proposal Date** and **Expiration** added by hand
(the 2026-05-27/28 "no date on the quotes" fix) but those edits were **not in the module**. A module
upgrade would have silently wiped them.

**After:** `report/sale_order.xml` now contains the Opportunity ID + **Proposal Date** + **Expiration**
title block, matching production, so re-deploying the module no longer regresses the date fix.

> ⚠️ **Production note:** A1 (Customer ID + enlarged logo) is **not present on the jun7 staging** I worked
> in — it looks like it was done on production only. Before we ever deploy this module to **production**,
> all live Studio report edits there (including your Customer ID + logo work) must be folded into
> `report/sale_order.xml` too, or the deploy will overwrite them. I can capture and fold them when we get to prod.

---

## 🟡 Awaiting your approval (not applied)

### B2 — Stop the opportunity name being overwritten ("OdooBot" / note text)
**Root cause (confirmed on staging):** server actions **1039 "Backfill Provider Payload"** and
**1047 "Lead BackFill Provider + Batch AI Field"** parse a name out of the latest email/message body and
run `vals['name'] = full_name; lead.write(vals)` **unconditionally**. A "last-resort" branch falls back to
the email display-name / address local-part. So whenever they re-run over a lead whose newest message is a
system note, a follow-up ("Quote sent by whatsapp. follow up"), or an OdooBot message, they **clobber a
good, human-entered opportunity name**.

**Proposed fix (surgical guard, identical in both actions):**
```python
# BEFORE
if full_name:
    vals[name_field] = full_name
    if contact_name_field in lead._fields:
        vals[contact_name_field] = full_name

# AFTER
if full_name:
    cur_name = (lead.name or "").strip()
    name_looks_auto = (
        (not cur_name)
        or ("@" in cur_name)
        or (cur_name.lower() in ("odoobot", "false", "none"))
        or (cur_name == (lead.email_from or ""))
        or (bool(lead.opportunity_file_id) and cur_name == lead.opportunity_file_id)
    )
    if name_looks_auto:                 # only set name if current one looks auto-generated/empty
        vals[name_field] = full_name
    if contact_name_field in lead._fields and not lead.contact_name:  # fill contact only if empty
        vals[contact_name_field] = full_name
```
**Effect:** a name typed/edited by a human is never overwritten; auto/blank names still get filled.
Lives in the DB (Studio), so it is applied via RPC on staging (original code backed up first), and
replicated on production later. **Reversible.**

### B1 — Terms & Conditions reliably present on every quote
**Root cause (confirmed on staging):** the **Quote HHG** and **Cartus** quotation templates have an
**empty** `note` (terms), while Art/Commercial/Agent/ITGBL/Gosselin carry full terms. On top of that, a
Studio automation **"Dynamic Terms"** rewrites the quote `note` via **AI** (`evaluation_type =
ai_computed`) on create/write — so terms can be blanked or changed unpredictably (this is exactly what
happened on S00501, an HHG/booker quote).

**Two options — please pick one:**
- **Option 1 (recommended, simplest/most reliable):** retire the AI "Dynamic Terms" automation; fill the
  empty templates (HHG, Cartus) with the correct standard **Included/Excluded** terms; rely on Odoo's native
  "load template → copy terms to quote". Terms become deterministic per template. *I need the canonical HHG
  Included/Excluded text from you (or I draft it from a known-good past HHG quote for your approval).*
- **Option 2 (dynamic by booker/scope):** keep terms rule-based but vary them by Booker vs Non-Booker ×
  service scope, applied on template load and on scope change (no AI). More moving parts; only worth it if
  the wording must differ within the same template.

### B3 — Lead **Source / Provider**: mandatory, auto-set, standardized
**Root cause (confirmed on staging):** `crm.lead.source_id` is **not required**, and there are ~50
inconsistent values (e.g. "Agent" / "Agent [2]", "call" / "Phone" / "Phone call"). The
`x_studio_source_provider` field is auto-detected from the inbound email (Expat Guidance / TriGlobal / MVF /
Quot8 / ReloAdvisor / Webs Form / Other) by the same backfill actions.

**Proposal — please approve the canonical list + rule:**
1. Consolidate the ~50 `utm.source` values into a short canonical list, e.g.
   **Expat Guidance, TriGlobal, MVF, Quot8, ReloAdvisor, Webs Form, Referral, Agent, Phone, Other**
   (mapping the messy ones into these). *Confirm/adjust this list.*
2. Make Source **required** on opportunities (view-level), and auto-populate it from the detected
   `x_studio_source_provider` on lead creation so it's filled without manual entry.
3. Optionally lock it to editable-by-managers-only once set.

---

## Deploy / status
- **A2, A3, drift-fix:** committed on `fix/green-staging-jun8`; **need a deploy to staging** (push +
  Odoo.sh rebuild of the `Jun7` build) before they're visible. Awaiting your go-ahead to push/merge.
- **B1, B2, B3:** awaiting your approval above; B2/B3/B1 are DB/Studio changes I apply via RPC on staging
  once approved.
