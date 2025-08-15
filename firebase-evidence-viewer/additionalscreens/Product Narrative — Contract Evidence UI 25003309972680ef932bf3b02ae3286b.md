# Contract Evidence UI — Build Instructions (v1.0.0)

### **Owner:** Scott

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

All panes resizable; SxS floats over chat.

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
/doc/{sha256}?page=12&bbox=126,532,419,557&field=base_rent&asof=2020-10-01

```

---

## 3) Source Reading Pane (Tabs + As-Of)

- **Tabs**: one per referenced document. Opening an answer **auto-opens** cited docs as tabs and focuses the first evidence span.
- **As-Of date picker** (pane header): defaults to the query’s date if present, else today.
    - Conformed view recomputes for that date; timeline chips: `Original → A1 → A2 → …` (click sets As-Of to the instrument’s effective date).
- **Viewer controls**: Zoom to selection • Toggle text layer • Darken page • Open full PDF • Copy page link • Find-in-doc • Prev/Next Evidence.

**Conformed tab is always present and labeled** `Conformed (As-Of YYYY-MM-DD)`.

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

**Actions**: **Edit** (HIL), **Save** (audit), **Compare to…** (pick date/instrument for right pane).

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
    
    **Blocked:** CAM evidence invalid. **Send to Review →**
    

---

## 6) Tables & Optional Drawer

- Table evidence → open the correct doc tab and highlight the **cell** (e.g., r3c2).
- *(Optional later)* **Evidence Drawer** icon on a table chip opens a lightweight grid (extracted CSV), highlights the source cell, and shows checksum (✅/⚠️). “Open in Document” jumps to the tab.
- Tabs remain the primary path; the drawer is just a speed boost.

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
- **Provenance:** every field has `doc_sha256`, `page`, `bbox` (or `cell`), `snippet`, `extractor`, `confidence`.

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
    {"label":"Base Rent","amount":10000.00,"evidence":[{"doc":"LEASE_2019.pdf","sha256":"…","page":12,"section":"§2.1(a)","bbox":[100,520,420,560]}]},
    {"label":"CAM","amount":4231.17,"evidence":[{"doc":"AMEND_1.pdf","sha256":"…","page":3,"table":{"row":3,"col":2,"title":"CAM Schedule"},"bbox":[210,320,280,340]}]},
    {"label":"Taxes","amount":1111.00,"evidence":[{"doc":"LEASE_2019.pdf","sha256":"…","page":18,"section":"Exhibit B","bbox":[140,200,390,230]}]}
  ],
  "formula":"total = base_rent + cam + taxes - credits",
  "tabs_to_open": ["LEASE_2019.pdf","AMEND_1.pdf"],
  "schema_version": "1.0.0"
}

```

**Evidence chip**

```json
{
  "display_doc":"Lease 2019",
  "sha256":"…",
  "page":12,
  "section":"§2.1(a)",
  "span_ids":["s1","s2"],
  "deep_link":"/doc/{sha256}?page=12&bbox=100,520,420,560&asof=2020-10-01",
  "status":"verified",
  "confidence":0.93,
  "schema_version":"1.0.0"
}

```

**SxS state**

```json
{
  "left":  { "type":"conformed", "as_of":"2020-10-01", "focus":{"clause_key":"lease.base_rent"} },
  "right": { "type":"document",  "doc_sha256":"…AMEND1…", "focus":{"page":3,"bbox":[210,320,280,340]} }
}

```

---

## 11) Keyboard & A11y

- `[` / `]` = prev/next evidence • `Enter` = open/focus • `Shift+Enter` = open SxS.
- Color-blind-safe highlight palette; optional hatched overlays.
- All chips and controls are keyboard reachable (ARIA roles/labels).

---

## 12) Telemetry & Audit

- Log: answer rendered, chip clicks (doc/page), SxS opens, HIL actions, deep-link copies.
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
    - **MAJOR**: Breaking UI behavior or payload changes.
    - **MINOR**: New optional features (e.g., Drawer).
    - **PATCH**: Copy/visual tweaks; no behavior change.
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
- **Backward compatibility window:** the frontend must support the current schema and the previous **minor** (X.Y-1).
- **Feature flags** (env or config) for optional features:
    - `feature.tableDrawer`
    - `feature.deltaCompare`
    - `feature.deepLinks` (on by default)

### 15.4 Migrations & Rollouts

- Any payload shape change ships behind a flag, with a **dual-path** renderer (old & new) for one release cycle.
- Add **contract tests** in CI: payload → render → click chip → verify focus & highlight.
- Release checklist must include: “No provenance → no answer” gates verified in staging.

### 15.5 Doc Header Block (put at top of this file)

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

![Screenshot 2025-08-15 073327.png](attachment:c411ba27-b415-424d-90e7-cf6ecbe2fa15:Screenshot_2025-08-15_073327.png)

## 15) Open Questions (for later)

- Do we want a “Delta” view between two arbitrary As-Of dates?
- Do we expose Bates numbers in the header when available?
- Drawer default: off (later A/B for speed vs uniformity).

[Requirements and Wireframe](https://www.notion.so/Requirements-and-Wireframe-2500330997268031b2eefba2d5079ab8?pvs=21)