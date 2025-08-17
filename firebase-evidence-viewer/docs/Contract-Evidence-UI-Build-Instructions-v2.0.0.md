# Contract Evidence UI — Build Instructions (v2.0.0)

**Owner:** Scott

**Purpose:** Lawyer-grade, time-aware contract answers with receipts.

**Golden rule:** **No provenance → no answer.**

**Scope:** Chat, Source Reading Pane (tabs), Side-by-Side (SxS), As-Of control, “Show Your Work” for calculations, HIL Editor, separate OCR Intake.

---

## 0) Goals

- Every answer is **verifiable**: click → open exact page, **highlight** the exact span or **table cell**.
- Time-aware: show **Conformed** agreement **as-of** a date (amendment overwrites; silence carries).
- Any calculation **shows its work** with links to **each operand’s** sources.
- HIL review exists but stays out of the user’s way.

---

## 1) Layout (3 areas)

- **Chat Window (left):** conversation + answers.
- **Source Reading Pane (center):** tabs for all referenced docs; page canvas + overlay highlights; **As-Of** date.
- **Side-by-Side** (full-width overlay): left = **Conformed (as-of)**; right = **Source Document** *or* **Delta** view.

*All panes are resizable; SxS floats over chat.*

---

## 2) Answer Composition & Evidence Chips

- In the answer text, the **citation itself is the link** (e.g., “…as per [§2.1(a)]”).
- **Evidence chips** render directly beneath each answer (minimal text):
    - `Lease 2019 • p12 • §2.1(a)`
    - `Amend. 1 • p3 • r3c2`
- **Click** chip → focus/open the correct tab in Source Reading Pane, scroll to span/cell, **flash highlight**.
- **Shift+Click** chip → open **SxS** (left = Conformed as-of; right = chip’s source doc).
- Chip hover: first 10–15 words of snippet.
- Chip context menu: **Copy deep link** • **Send to Review**.

**Deep link format**

```
/doc/{sha256}?page=12&bbox=126,532,419,557&field=base_rent&asof=2020-10-01&exp=1734390000&sig=<hmac>

```

> Note: bbox is x0,y0,x1,y1 in PDF user-space (origin bottom-left), comma-separated integers after rounding.
> 

---

## 3) Source Reading Pane (Tabs + As-Of)

- **Tabs:** one per referenced document. Opening an answer **auto-opens** cited docs as tabs and focuses the first evidence span.
- **As-Of date picker** (pane header): defaults to the query’s date if present, else **today**.
    - Conformed view recomputes for that date; timeline chips: `Original → A1 → A2 → …` (click sets As-Of to the instrument’s effective date).
    - **Display timezone:** *America/Los_Angeles* (consistent across UI and URLs).
- **Viewer controls:** Zoom to selection • Toggle text layer • Darken page • Open full PDF • Copy page link • Find-in-doc • Prev/Next Evidence.

**Conformed tab is always present and labeled** `Conformed (As-Of YYYY-MM-DD, America/Los_Angeles)`.

---

## 4) Side-by-Side (SxS) — Provenance & Diffs

**Pane types**

- **Conformed** — shows contract **as-of** a date; **has date picker** in that pane.
- **Source Document** — shows a specific PDF (lease/amendment/exhibit); **no date picker** (immutable).

**Patterns**

- Conformed@T1 ↔ Conformed@T2 (time-travel)
- Conformed@T ↔ Source Amendment (default provenance)
- Conformed@today ↔ Original Lease PDF

**Behavior**

- **Sync scroll** on; if both Conformed, sync by clause; if right is a doc, center on that doc’s evidence span.
- Clicking a revised clause on the left jumps the right pane to the **authorizing span**.

**Actions:** **Edit** (HIL), **Save** (audit), **Compare to…** (pick date/instrument for right pane).

---

## 5) Calculation Transparency Rule (CTR)

If an answer includes a derived number from **≥ 2 sources** (even within the same doc), the UI **must show the work**:

- **Breakdown card** under the answer (always visible):
    
    `Total (Oct 2020) = Base Rent + CAM + Taxes − Credits`
    
    Each line shows the amount **and its chip(s)**.
    
- **Formula trace** (inline):
    
    `= 10000.00 + 4231.17 + 1111.00 − 0.00 = 15342.17` **✓ Verified**
    
- Every operand links to **its exact span/cell** (tables include row/col).
- **Gate:** If any operand lacks verifiable evidence or fails validation, **do not display** the total. Render:
    
    **Blocked:** `<operand>` evidence missing/invalid. **Send to Review →**
    

---

## 6) Tables & Optional Drawer

- Table evidence → open the correct doc tab and highlight the **cell** (e.g., r3c2).
- *(Optional later)* **Evidence Drawer** icon on a table chip opens a lightweight grid (extracted CSV), highlights the source cell, and shows checksum (✅/⚠️). “Open in Document” jumps to the tab.
- Tabs remain the primary path; the drawer is a speed boost only.

---

## 7) HIL (Human-in-the-Loop) Editing

- **HIL runs in SxS.** Click **Edit** to enable **structured** edits on the Conformed pane:
    - **Accept** • **Correct (enter value)** • **Upload better scan** • **Ignore (boilerplate)**
    - Saving creates a **ClauseVersion** or **human extraction** with provenance and **audit log** (user, time, reason).
    - Free-text overrides are watermarked **Manual Override** and require a reason.
- HIL corrections **re-run validator** and update Conformed + Answers immediately.

---

## 8) OCR / Intake (Separate Page)

- **Document Intake** prior to analysis:
    - Queue with statuses (Needs OCR, Needs Review, Ready).
    - Per-page viewer with **low-confidence heatmap**.
    - Actions: **Transcribe / Upload better scan / Ignore**.
    - Quality metrics (dpi, skew, contrast).
    - **Promote to Analysis** only after validator passes.

---

## 9) Validation & Gating (must pass before display)

- **Arithmetic:** evaluate expression tree using **decimal**; round only at display.
- **Units:** normalize currencies/units; no mixing without explicit conversion evidence.
- **Tables:** verify cell exists; optional totals reconcile → badge ✅/⚠️.
- **Temporal:** As-Of resolver picks correct ClauseVersion; overlaps ⇒ conflict ⇒ HIL.
- **Provenance:** every field has `sha256`, `page`, `bbox` (or `cell`), `snippet`, `extractor`, `confidence`.

> No provenance → no answer.
> 

---

## 10) Data Contracts (Frontend expects)

**Answer payload**

```json
{
  "as_of": "2020-10-01",
  "answer": "Total rent (Oct 2020): $15,342.17",
  "breakdown": [
    {
      "label": "Base Rent",
      "amount": 10000.00,
      "evidence": [
        {
          "doc": "LEASE_2019.pdf",
          "sha256": "…",
          "page": 12,
          "section": "§2.1(a)",
          "bbox": [100, 520, 420, 560]
        }
      ]
    },
    {
      "label": "CAM",
      "amount": 4231.17,
      "evidence": [
        {
          "doc": "AMEND_1.pdf",
          "sha256": "…",
          "page": 3,
          "table": { "row": 3, "col": 2, "title": "CAM Schedule" },
          "bbox": [210, 320, 280, 340]
        }
      ]
    },
    {
      "label": "Taxes",
      "amount": 1111.00,
      "evidence": [
        {
          "doc": "LEASE_2019.pdf",
          "sha256": "…",
          "page": 18,
          "section": "Exhibit B",
          "bbox": [140, 200, 390, 230]
        }
      ]
    }
  ],
  "formula": "total = base_rent + cam + taxes - credits",
  "tabs_to_open": ["LEASE_2019.pdf", "AMEND_1.pdf"],
  "schema_version": "1.0.0"
}

```

**Evidence chip**

```json
{
  "display_doc": "Lease 2019",
  "sha256": "…",
  "page": 12,
  "section": "§2.1(a)",
  "span_ids": ["s1", "s2"],
  "deep_link": "/doc/{sha256}?page=12&bbox=100,520,420,560&asof=2020-10-01&exp=1734390000&sig=<hmac>",
  "status": "verified",
  "confidence": 0.93,
  "schema_version": "1.0.0"
}

```

**SxS state**

```json
{
  "left":  { "type": "conformed", "as_of": "2020-10-01", "focus": { "clause_key": "lease.base_rent" } },
  "right": { "type": "document",  "sha256": "…AMEND1…", "focus": { "page": 3, "bbox": [210, 320, 280, 340] } }
}

```

---

## 11) Keyboard & A11y

- `[` / `]` = prev/next evidence • `Enter` = open/focus • `Shift+Enter` = open SxS.
- Color-blind-safe highlight palette; optional hatched overlays.
- All chips and controls are keyboard reachable (ARIA roles/labels).

---

## 12) Telemetry & Audit

- Log: `answer_rendered`, `chip_clicked`, `sxs_opened`, `hil_action`, `deep_link_copied`, `asof_changed`.
- Show **SHA-256** and source system **in the Source Pane header** (not on chips).

---

## 13) Non-Functional

- Pre-render thumbnails & page PNGs; cache by `sha256`.
- PDF.js + overlay canvas; store bboxes in **PDF user space**; transform via viewport (handles rotation).
- Lazy-load heavy features (SxS, history, optional drawer).

---

## 14) Acceptance Criteria (MVP)

- Clicking any citation or chip opens the **correct tab** and highlights the **exact** span/cell.
- Changing **As-Of** re-resolves Conformed content, highlights, and math.
- Derived numbers display **breakdown + formula trace** with chips; validator ✓ before display.
- SxS shows **Conformed (As-Of)** vs **Source** with sync scroll.
- Missing/invalid evidence **blocks** the answer and creates a Review task.

---

## 15) Version Control & Change Management

### 15.1 Spec & UI Versioning

- Use **Semantic Versioning** for this doc & UI behavior: **MAJOR.MINOR.PATCH**.
    - **MAJOR:** Breaking UI behavior or payload changes.
    - **MINOR:** New optional features (e.g., Drawer).
    - **PATCH:** Copy/visual tweaks; no behavior change.
- Add a version header to this document and a `schema_version` field to every payload (see examples).

### 15.2 Git Branching & Releases

- **Default branch:** `main` (stable).
- **Active dev:** `develop`.
- **Feature branches:** `feature/<short-name>` → PR to `develop`.
- **Release branches:** `release/x.y.0` → harden → tag `vX.Y.0` → merge to `main` & back-merge to `develop`.
- **Hotfix:** `hotfix/x.y.z` from `main`, tag `vX.Y.Z`.

Include:

- `.github/PULL_REQUEST_TEMPLATE.md` (acceptance checklist + screenshots/gifs).
- `CHANGELOG.md` with Keep-a-Changelog format.
- `CODEOWNERS` to route reviews.

### 15.3 API & Schema Compatibility

- The **Answer payload** and **Evidence chip** include `schema_version`.
- **Backward compatibility window:** the frontend must support the current schema and the previous **minor** (X.Y−1).
- **Feature flags** (env or config) for optional features:
    - `feature.tableDrawer`
    - `feature.deltaCompare`
    - `feature.deepLinks` (on by default)

### 15.4 Migrations & Rollouts

- Any payload shape change ships behind a flag, with a **dual-path** renderer (old & new) for one release cycle.
- Add **contract tests** in CI: payload → render → click chip → verify focus & highlight.
- Release checklist must include: “No provenance → no answer” gates verified in staging.

### 15.5 Doc Header Block (copy/paste at top)

```
Spec: Contract Evidence UI
Version: 1.0.0
Owner: Scott
Last updated: YYYY-MM-DD
Change summary: Initial consolidated spec

```

---

## 16) Testing

### 16.1 Scenarios (happy path)

- Single-doc single-span citation.
- Multi-doc multi-span (Lease + two Amendments).
- Table cell origin (r3c2) with checksum ✅.
- As-Of set by query date; change to today; chips still resolve.

### 16.2 Edge cases

- Amendment silent on a clause (carry-forward).
- Overlapping ClauseVersions (conflict → HIL).
- Proration (mid-month start): expression tree shows factors & sources.
- No span found for an operand (Blocked UI state).

### 16.3 Performance

- Open answer that cites 3 docs: tabs appear < 300ms (from cache).
- SxS open < 500ms on cached pages.
- Rendering highlights on rotated pages is correct.

---

## 17) Routing & Deep-Link Parsing

**Chip target model**

```json
{
  "target": "conformed" | "document",
  "as_of": "YYYY-MM-DD",
  "sha256": "…",             // required for target=document
  "page": 12,
  "bbox": [126, 532, 419, 557],
  "cell": { "row": 3, "col": 2 } // when table-derived
}

```

**Deep link URL**

```
/doc/{sha256}?page=12&bbox=126,532,419,557&field=base_rent&asof=2020-10-01&exp=1734390000&sig=<hmac>

```

**Router rules**

- If `asof` present → focus **Conformed** tab at that date; also open cited **source doc** tab(s).
- If `sha256` present → open **Document** tab and scroll highlight to `bbox`.
- **Shift+Click** on any chip → open SxS with left=Conformed(as-of), right=Document(sha256).

---

## 18) Highlight Rendering Spec

- Store bboxes in **PDF user space** (origin bottom-left).
- Use PDF.js `page.getViewport({ scale })` and `Util.applyTransform` to map to screen.
- **Rotation:** never pre-rotate bboxes; viewport handles it.
- **Multi-span:** draw N rectangles per evidence; use one tint per field.
- **Focus flash:** animate alpha 0→0.35→0.15 over 600ms.
- **Find-in-doc:** when user searches, render dashed boxes (not the solid evidence tint).

---

## 19) Security & Access

- **Signed preview URLs** with TTL (e.g., 10 min); include `user_id`, `tenant_id`, `sha256`, `exp`, and HMAC.
- **Row-level ACL:** tenant_id + per-doc access; validate on every deep link open.
- **Redaction flag** on export/print; originals stay immutable.
- **Audit log** events (see §21): include `user_id`, `sha256`, `page`, `field`.

---

## 20) Error & Empty States

- **Blocked calculation:** render a red banner under the answer:
    
    `Blocked: <operand> evidence missing/invalid.` **Send to Review →**
    
- **Doc not found / access denied:** toast + keep user in current tab; show a disabled chip state.
- **No highlight match** (bbox outside page): show a yellow banner “Span out of bounds; opening page start” and auto-scroll to top.
- **As-Of has no conformed value:** gray panel “No active version at this date.” Show history chips.

---

## 21) Event Telemetry (names & payloads)

- `answer_rendered` `{answer_id, as_of, doc_count}`
- `chip_clicked` `{sha256, page, field, as_of, with_shift}`
- `sxs_opened` `{left_type, left_as_of, right_type, sha256?}`
- `asof_changed` `{from, to}`
- `hil_action` `{action: accept|correct|upload|ignore, field, sha256, page}`
- `deep_link_copied` `{sha256, page, field}`

---

## 22) Test Hooks & Smoke Tests

**Add these `data-testid`s**

`answer-citation`, `evidence-chip`, `asof-date`, `tab-conformed`, `tab-document`, `highlight-span`, `open-sxs`, `breakdown-row`, `prev-evidence`, `next-evidence`.

**Playwright smoke (outline)**

```tsx
test('chips route to correct tab and highlight', async ({ page }) => {
  await page.click('[data-testid="evidence-chip"]:has-text("Lease 2019 • p12")');
  await expect(page.getByTestId('tab-document')).toContainText('LEASE_2019.pdf');
  await expect(page.getByTestId('highlight-span')).toBeVisible();
});

test('as-of re-renders conformed & keeps source tabs', async ({ page }) => {
  await page.fill('[data-testid="asof-date"] input', '2020-10-01');
  await page.keyboard.press('Enter');
  await expect(page.getByTestId('tab-conformed')).toContainText('As-Of 2020-10-01');
});

```

---

## 23) TypeScript Interfaces (UI)

```tsx
export type PaneType = 'conformed' | 'document';

export interface EvidenceRef {
  doc: string;
  sha256: string;
  page: number;
  bbox: [number, number, number, number];
  section?: string;
  table?: { row: number; col: number; title?: string };
}

export interface BreakdownItem {
  label: string;
  amount: number;
  evidence: EvidenceRef[];
  status?: 'verified' | 'warn' | 'blocked';
}

export interface AnswerPayload {
  as_of: string; // YYYY-MM-DD
  answer: string;
  breakdown: BreakdownItem[];
  formula: string;
  tabs_to_open: string[];
  schema_version: string;
}

export type ConformedPane = { type: 'conformed'; as_of: string; focus?: { clause_key?: string } };
export type DocumentPane  = { type: 'document' ; sha256: string;  focus?: { page?: number; bbox?: [number, number, number, number] } };

export interface SxSState {
  left:  ConformedPane;
  right: DocumentPane | ConformedPane;
}

```

---

## 24) Minimal Backend Endpoints (UI Contracts)

- `GET /answers/:id` → `AnswerPayload` (with breakdown & evidence).
- `GET /documents/:sha256/pages/:p/preview` → PNG (cached).
- `GET /documents/:sha256/pdf` → full PDF stream.
- `POST /deep-link/resolve` `{ url }` → `{ target, as_of, sha256, page, bbox }` (server validates signature & ACL).
- `POST /hil/task` `{ sha256, page, bbox, reason, field }` → `{ task_id }`.
- `GET /conformed?as_of=YYYY-MM-DD&deal_id=…` → rendered conformed HTML/chunks (or IDs to render client-side).

*All responses include `Cache-Control` for previews; 401/403 for ACL failures.*

---

## 25) Date Policy (As-Of Semantics)

- **Timezone:** default **America/Los_Angeles**; render As-Of in that zone.
- **Effective date precedence:**
    1. explicit clause “effective upon …” date;
    2. instrument **effective_date**;
    3. **recording** timestamp (tie-breaker).
- Same-day multiple instruments → use recording time or explicit sequence; if ambiguous, mark **conflict** and require HIL.

---

## 26) Currency & Rounding

- Internal math uses **decimal**; round only for display.
- Display format: `$#,###.##` (2 decimals unless operand evidence specifies precision).
- Mixed currency requires explicit conversion evidence (rate, date, source) or is **blocked**.

---

## 27) Release Hygiene

- Frontend supports current and previous **minor** `schema_version`.
- Features behind flags: `feature.tableDrawer`, `feature.deltaCompare`, `feature.deepLinks` (default on).
- CI contract tests:
    - Payload → render → chip click → tab focus & highlight present.
    - As-Of change re-renders Conformed and preserves source tabs.
    - SxS opens with correct pane types and no date picker on source docs.

![Screenshot 2025-08-15 073327.png](Screenshot_2025-08-15_073327.png)