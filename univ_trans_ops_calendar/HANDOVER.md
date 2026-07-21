# Universe Transit — Operations Calendar: Developer Transfer Document

**Module:** `univ_trans_ops_calendar` · **Version:** 1.0 → **1.1**
**Repo:** `ScaleUpRight/univ-trans` · **Branch:** `jul13`
**Depends on:** `project`, `sale`, `mail`, `univ_trans_customisation`
**Date:** 2026-07-21

This is the companion to your `UnivTrans_OpsCalendar_E2E_Test` README. It documents the changes
made on top of your v1.0 so the module matches the **original operations-calendar design** agreed
with the client, and hands the work back to you for testing and deployment.

---

## 1. Why the change

Your v1.0 turned a confirmed sale order into **one** umbrella job on the matching project. The
client's locked design is different: **each operational activity** needed to fulfil a move
(Survey, Packing, Pickup, Customs, the freight leg, Delivery…) must be its **own task on the
calendar**, so the dispatch team can schedule and track each leg independently.

So v1.1 replaces the single-job creation with a **per-activity generator**, adds **automatic
scheduling** (so cards actually appear on the calendar), computes the region from data that
already exists, and drops a redundant field.

---

## 2. v1.0 vs. v1.1 (what actually changed)

| Area | v1.0 (yours) | v1.1 (this handover) |
|------|--------------|----------------------|
| Jobs per SO | One umbrella task | **One task per activity** driven by a rule matrix |
| Region | New manual field `x_ops_region` (Selection) on the SO | **Removed** — region is **computed** from existing fields |
| Scheduling | No dates set → cards never appeared on the calendar until dragged | **Auto-dated** via native `planned_date_begin` / `date_deadline`, anchored on the SO Delivery Date |
| Calendar colour | Inherited default | **Coloured by activity type** (`x_studio_service_type`) |
| Service type | Not set on the created task | Set per generated activity |
| Kept as-is | Dispatch auto-follow, confirmation email on "Confirmed", manager-only delete, duplicate guard | All retained |

No new fields were added and no new module was created — everything stays inside
`univ_trans_ops_calendar`.

---

## 3. Design decisions (locked with the client)

1. **Use existing fields only.** The task `service_type` keeps its current Studio values
   (`Packing / Pickup / Delivery / Survey / Customs / Storage / Other`). No `Freight`/`Export`/
   `Import` values were added, even though the original mockup showed them.
2. **Region is derived, not entered.** Rule:
   - `shipment_direction` = **Export** or **Import** → **International**
   - `shipment_direction` = **Local** → **Israel**
   - `shipment_direction` = **Drop** / blank → decided by the **country** fields
     (International if any leg is outside Israel).
3. **Activities come from the scope booleans** already computed on the sale order
   (`x_studio_origin` / `x_studio_freight` / `x_studio_destination`).
4. **Dates** anchor on the sale order's native **Delivery Date** (`commitment_date`), with per-leg
   day offsets. Falls back to `date_order` when empty.
5. **Storage is parked** for now (it lives inside `service_scope`; revisit later).

---

## 4. The activity matrix (reference)

Anchor = the "move day" `M` (SO `commitment_date`, else `date_order`). Offsets/durations are the
current **defaults** — expected to be tuned with the ops team.

| Condition | Activities generated (service_type, offset, hours) |
|-----------|-----------------------------------------------------|
| `x_studio_origin` | Survey (M−7, 2h) · Packing (M−1, 8h) · Pickup (M+0, 4h) |
| `x_studio_freight` **and** region = International | Customs (M+1, 4h) · **Other** = freight leg (M+2, 8h) |
| `x_studio_destination` | Delivery (M+1 local / M+14 international, 4h) |

The matrix is defined as plain constants at the top of `models/sale_order.py`
(`ORIGIN_ACTIVITIES`, `FREIGHT_ACTIVITIES`) so it is easy to adjust.

---

## 5. Files changed

- `models/sale_order.py` — removed `x_ops_region`; replaced `_create_ops_calendar_task` with a
  per-activity generator. New helpers: `_get_ops_region`, `_ops_activity_plan`,
  `_ops_base_datetime`, `_prepare_ops_task_vals`, `_generate_ops_activities`.
- `views/sale_order_views.xml` — removed the "Operations / Calendar Settings" region field group
  (smart button kept).
- `views/project_task_views.xml` — calendar now `color="x_studio_service_type"`.
- `__manifest__.py` — version 1.0 → 1.1; summary updated.

`models/project_task.py`, the projects/stages data, the security group, and the mail template are
**unchanged** from your v1.0.

---

## 6. Open items for you

1. **Tune the date offsets and durations** in `sale_order.py` against how the ops team really
   sequences a move.
2. **Country fallback:** the Drop/blank branch string-matches the country text
   (`israel / il / isr / ישראל`). Those `x_studio_*_country` fields are free text today — a
   separate project will convert them to proper `res.country` dropdowns, after which swap the
   match for `country_id.code == 'IL'`.
3. **Freight leg under "Other":** confirm with the client or drop it.
4. **Studio dependency:** `x_studio_service_type` must exist on `project.task` with those exact
   values (it does wherever this module was already installed, since your filters use them).
5. **Timezone:** start times are set at 08:00 UTC; consider converting to the company timezone.
6. **"Auto Job Name" Studio automation:** if that server action is still active in the target DB,
   it may re-derive the task `name` on create/write — reconcile it with the new `[SO] Activity –
   Customer` naming so they don't fight.

---

## 7. How to test (quick pass)

1. On an **opportunity**, set the scope so at least one of origin/freight/destination is true, and
   set `shipment_direction` (try Local, then Export).
2. Create a quotation from it, set a **Delivery Date**, and **Confirm** it.
3. Expect **multiple tasks** (one per activity from the matrix), in the correct project
   (Israel vs International), each with a **Start/End date**, in the **Planned** stage.
4. Open the **calendar** → cards appear at their scheduled times, **coloured by activity type**.
5. Move a task to **Confirmed** → customer confirmation email fires (partner must have an email).
6. Try to delete a task as a non-manager → blocked; as a project manager → allowed.
7. Re-confirm the same SO → **no duplicate** tasks.

---

## 8. Deployment

- Changes are committed on **`jul13`**. Build/refresh a staging environment **from `jul13`**,
  then **upgrade** the `univ_trans_ops_calendar` module (version bump to 1.1 forces the reload).
- The module's projects/stages are created via `noupdate` data, so an existing install keeps its
  data; only the new logic/views load.
- **Not yet run inside Odoo** — needs an install + the test pass above on staging before prod.
