# OCR + HIL Ingestion Pipeline (Lane A) — v1.1

**Owner:** Scott

**Purpose:** Build a two-lane ingestion pipeline with a production-ready "Lane A" fast path and an integrated Human‑in‑the‑Loop (HIL) quality gate. Output is a structured, verifiable JSON contract consumed by downstream agentic reasoning.

---

## 1) High‑Level Goals & Principles

- **Provenance is paramount.** Every datum traces back to **file → page → bbox** (PDF points). No provenance → no answer.
- **Two lanes.** Default to **Lane A** (fast, automated). Escalate to **Lane B** (deep processing) only when quality or structure fails.
- **Agentic orchestration.** A state machine (e.g., **LangGraph**) routes documents between specialized workers based on metrics and rules.
- **HIL as a quality gate.** Low confidence automatically creates review tasks; human inputs are versioned, auditable, and re‑ingested.

---

## 2) End‑to‑End Dataflow (Lane A + HIL)

```
User Upload → Ingestion API → Normalizer → Router
   ├─[has text layer OR good OCR]→ Lane A
   │   ├─ Partition (Unstructured)
   │   ├─ Heuristic Extract (spaCy + regex)
   │   ├─ JSON Contract Build
   │   └─ Validate → Emit
   └─[no/low text layer]→ OCR Worker (ocrmypdf + tesseract TSV)
        ├─ score pages → if page/doc score < threshold → HIL Task(s)
        │     └─ HIL UI (Transcribe/Upload/Ignore) → Audit → Corrections store
        └─ back to Lane A with corrected text overlays

```

---

## 3) Components (initial build scope)

- **Storage:** MinIO/S3 for blobs (original + normalized PDF, page PNGs, OCR TSVs, tables CSVs).
- **DB:** Postgres for documents, pages, elements, tasks, edits, audit trail, processing runs.
- **Queue/Bus:** Redis (RQ) or RabbitMQ. Simple is fine; pick one.
- **Orchestrator:** LangGraph (Python) state machine controlling transitions.
- **Workers:**
    - **Normalizer:** Convert any input → standard PDF; preserve original; compute SHA‑256.
    - **Router:** Detect native text layer; estimate dpi; sample text density.
    - **OCR:** `ocrmypdf --deskew --rotate-pages --clean` + **Tesseract** TSV/HOCR per page.
    - **Partition:** Unstructured → typed elements with page + bbox; export tables to CSV.
    - **Heuristics:** spaCy NER + regex for parties/dates/amounts → `quick_facts`.
- **API:** FastAPI for ingestion, task list, HIL actions, document retrieval.
- **UI:** Minimal HIL reviewer (two‑pane with highlights + action form).

---

## 4) State Machine (LangGraph) — v1

**States:** `INGESTED → NORMALIZED → ROUTED → OCR → HIL_PENDING? → LANE_A → VALIDATE → EMIT`

**Transitions (rules):**

- `ROUTED → LANE_A` if native text layer exists **OR** `ocr_score_doc ≥ 0.85` **AND** no page with `ocr_score_page < 0.8`.
- `OCR → HIL_PENDING` if any page `ocr_score_page < 0.8`, **OR** doc `ocr_score_doc < 0.85`, **OR** dpi_est < 200, **OR** text coverage < 5%.
- `HIL_PENDING → LANE_A` when all blocking tasks resolved.
- `LANE_A → HIL_PENDING` if downstream validators fail (e.g., table parse fails on >40% cells, or date/amount anomalies).
- `VALIDATE → EMIT` on schema + provenance checks; otherwise bounce to `HIL_PENDING` with reasons.

---

## 5) API (FastAPI) — minimal contract

### Ingest

- **POST** `/ingest`
    
    **Body:** multipart file + optional `source_uri`
    
    **Resp:** `{ doc_id, sha256, status: "INGESTED" }`
    

### Document & Elements

- **GET** `/documents/{doc_id}` → metadata + current status + quality + provenance + quick_facts
- **GET** `/documents/{doc_id}/elements?type=table|paragraph|...` → paginated element list

### HIL Tasks

- **GET** `/hil/tasks?status=pending` → reviewer queue
- **GET** `/hil/tasks/{task_id}` → `{page, bbox, image_url, ocr_text, reason, suggested_label}`
- **POST** `/hil/tasks/{task_id}/transcribe` → `{text, offsets?}` (links to page+bbox)
- **POST** `/hil/tasks/{task_id}/upload` → supplemental file (advanced; can stub)
- **POST** `/hil/tasks/{task_id}/ignore` → `{reason}` (e.g., smudge/stamp/irrelevant)
- **POST** `/hil/tasks/{task_id}/complete` → closes task, routes doc forward

> All write endpoints append to audit_log with actor, timestamp, action, payload hash.
> 

---

## 6) Data Model (Postgres)

**documents**

- `doc_id UUID PK`, `sha256 text unique`, `source_uri text`, `ingest_time timestamptz`, `pages int`, `doc_type_guess text`, `status text`, `quality jsonb`, `provenance jsonb`

**document_files**

- `doc_id FK`, `kind enum('original','normalized','page_png','ocr_tsv','table_csv')`, `path text`, `page int?`, `created_at`

**pages**

- `doc_id FK`, `page int`, `dpi_est int`, `ocr_score numeric`, `text_coverage numeric`, `flags text[]`

**elements**

- `element_id UUID PK`, `doc_id FK`, `page int`, `type text`, `bbox jsonb`, `text text`, `meta jsonb`

**quick_facts**

- `id PK`, `doc_id FK`, `label text`, `value text`, `page int`, `element_id UUID?`, `confidence numeric`

**processing_runs**

- `run_id PK`, `doc_id FK`, `state text`, `started_at`, `ended_at`, `metrics jsonb`, `error text?`

**hil_tasks**

- `task_id PK`, `doc_id FK`, `page int`, `bbox jsonb`, `reason text`, `status enum('pending','resolved','ignored')`, `created_at`, `resolved_at?`, `assignee text?`

**hil_edits**

- `edit_id PK`, `task_id FK`, `action enum('transcribe','upload','ignore')`, `payload jsonb`, `actor text`, `created_at`

**audit_log**

- `log_id PK`, `doc_id FK`, `actor text`, `action text`, `payload_hash text`, `created_at`

---

## 7) Filesystem Layout (MinIO/S3 keys)

```
/blobs/{doc_id}/original/{filename.ext}
/blobs/{doc_id}/normalized/document.pdf
/blobs/{doc_id}/pages/{page}.png
/blobs/{doc_id}/ocr/{page}.tsv
/blobs/{doc_id}/tables/t{n}.csv

```

---

## 8) OCR Scoring & HIL Triggers

- **Per‑token score:** from Tesseract TSV `conf` (0–100, -1 for non‑word). Ignore -1.
- **Page score:** mean(conf)/100 across tokens; require ≥ **0.80**.
- **Doc score:** weighted mean(page_score by token count); require ≥ **0.85**.
- **Ancillary checks:**
    - `dpi_est < 200` → HIL
    - `text_coverage < 5%` (very sparse) → HIL
    - Excessive low‑ASCII or broken glyph ratio (>25%) → HIL
    - Table parse failure on >40% rows/cells → HIL

**Highlight regions:** aggregate contiguous low‑conf tokens into spans → compute bbox union → create one HIL task per region per page (cap at e.g. 10 per page).

---

## 9) Lane A Processing Details

**Partition:** Unstructured `partition_pdf` with coordinates; capture `id`, `type`, `page`, `bbox`, and `text`. Persist tables as CSV; link via `elements.meta.csv_ref`.

**Heuristic Extraction:**

- Parties: `ORG`/`PERSON` (spaCy) + header heuristics ("This Agreement is entered into by and between …").
- Dates: regex for `YYYY‑MM‑DD`, `Month D, YYYY`, `effective|execution` labels.
- Amounts: currency regex + nearby labels (`purchase price`, `rent`, `penalty`, `deposit`).
- Output to `quick_facts` with `label`, `value`, `page`, `element_id?`, `confidence`.

**Validation:** JSON schema check (see §11) + provenance check (every fact must have page/bbox or be explicitly `derived`). If missing → bounce to HIL with `reason="missing_provenance"`.

---

## 10) HIL Reviewer UI (MVP Spec)

**Layout:**

- **Left pane:** page PNG with highlighted bbox regions (click to zoom). Page nav.
- **Right pane:** task details + form:
    - **Transcribe** (textarea) → saves text + offset link
    - **Upload** (optional) → adds supplemental evidence (deferred in MVP)
    - **Ignore** (dropdown reason: stamp, smudge, boilerplate, other)
- **Keyboard:** `Enter=save`, `Tab=next task`, `I=ignore`, `Z=zoom`.

**Task payload (GET):**

```json
{
  "task_id": "...",
  "doc_id": "...",
  "page": 7,
  "bbox": [72, 518, 312, 566],
  "image_url": ".../pages/7.png",
  "ocr_text": "S@nt@ Cl@r@ C0unty",
  "reason": "low_confidence",
  "suggested_label": "county_name?"
}

```

**Transcribe (POST):**

```json
{
  "text": "Santa Clara County",
  "char_offsets": {"start": 0, "end": 20}
}

```

→ creates `hil_edits` record, updates `elements` (or creates `corr_overlay` element), reruns Lane A on this page’s text.

---

## 11) Lane A JSON Contract — JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/laneA.contract.schema.json",
  "title": "LaneAContract",
  "type": "object",
  "required": ["doc_id","pages","elements","quality","provenance"],
  "properties": {
    "doc_id": {"type":"string","format":"uuid"},
    "doc_type_guess": {"type":"string","enum":["Lease","PSA","DA","Amendment","Title","Unknown"]},
    "pages": {"type":"integer","minimum":1},
    "elements": {
      "type":"array",
      "items": {
        "type":"object",
        "required":["id","type","page","bbox"],
        "properties": {
          "id": {"type":"string"},
          "type": {"type":"string","enum":["heading","paragraph","list_item","table","figure","footnote","formula","other"]},
          "text": {"type":["string","null"]},
          "page": {"type":"integer","minimum":1},
          "bbox": {"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4},
          "csv_ref": {"type":["string","null"]},
          "meta": {"type":"object","additionalProperties":true}
        }
      }
    },
    "quick_facts": {
      "type":"object",
      "properties": {
        "parties": {"type":"array","items":{"type":"object","properties":{
          "text":{"type":"string"},"page":{"type":"integer"},"element_id":{"type":["string","null"]},"confidence":{"type":["number","null"]}
        }}}
        ,"dates": {"type":"array","items":{"type":"object","properties":{
          "label":{"type":"string"},"value":{"type":"string","format":"date"},"page":{"type":"integer"},"element_id":{"type":["string","null"]},"confidence":{"type":["number","null"]}
        }}}
        ,"amounts": {"type":"array","items":{"type":"object","properties":{
          "label":{"type":"string"},"value":{"type":"string"},"page":{"type":"integer"},"element_id":{"type":["string","null"]},"confidence":{"type":["number","null"]}
        }}}
      },
      "additionalProperties":true
    },
    "quality": {
      "type":"object",
      "required":["ocr_score","dpi_est","flags"],
      "properties": {
        "ocr_score": {"type":"number","minimum":0,"maximum":1},
        "dpi_est": {"type":"integer"},
        "flags": {"type":"array","items":{"type":"string"}}
      }
    },
    "provenance": {
      "type":"object",
      "required":["sha256","ingest_time","source_uri"],
      "properties": {
        "sha256": {"type":"string"},
        "ingest_time": {"type":"string","format":"date-time"},
        "source_uri": {"type":"string"}
      }
    }
  }
}

```

**Example (abbrev):**

```json
{
  "doc_id": "6a27b4c1-33f9-4a9c-9cda-3b6a3f1c2e8d",
  "doc_type_guess": "PSA",
  "pages": 15,
  "elements": [
    {"id":"e123","type":"paragraph","text":"This Purchase and Sale Agreement…","page":1,"bbox":[72,700,540,760]},
    {"id":"t4","type":"table","csv_ref":"s3://…/tables/t4.csv","page":12,"bbox":[90,120,520,540]}
  ],
  "quick_facts": {
    "parties":[{"text":"Acme LLC","page":1,"element_id":"e123","confidence":0.92}],
    "dates":[{"label":"effective_date_guess","value":"2019-02-01","page":1,"element_id":"e123","confidence":0.78}],
    "amounts":[{"label":"purchase_price_guess","value":"$3,250,000","page":2,"element_id":null,"confidence":0.66}]
  },
  "quality": {"ocr_score": 0.98, "dpi_est": 300, "flags": ["deskewed"]},
  "provenance": {"sha256": "…", "ingest_time": "2025-08-17T10:45:01Z", "source_uri": "minio://bucket/originals/foo.pdf"}
}

```

---

## 12) Validators (MVP)

- Schema validity (JSON Schema above) and required fields present.
- Provenance completeness: **every element** must include page + bbox; every `quick_fact` should reference `element_id` when possible.
- Sanity checks: dates in plausible range (1900–2100), amounts parseable as currency, page indexes in range, bbox inside page box.
- Table sanity: CSV row/column counts > 0; header cells text coverage > 50%.

Failures → create `hil_tasks` with `reason` (`schema_violation`, `bad_bbox`, `table_parse_fail`, etc.).

---

## 13) DevOps Scaffolding (docker-compose excerpt)

```yaml
version: "3.9"
services:
  api:
    build: ./services/api
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ingestion
      - MINIO_ENDPOINT=minio:9000
      - QUEUE_URL=redis://redis:6379/0
    depends_on: [db, minio, redis]

  worker:
    build: ./services/worker
    environment: *environment
    depends_on: [api]

  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=postgres
    ports: ["5432:5432"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000","9001:9001"]

  redis:
    image: redis:7

```

**Recommended env:**

- `OCR_LANGS="eng+spa"` as needed
- `OCR_PAGE_SCORE_THRESHOLD=0.80`, `OCR_DOC_SCORE_THRESHOLD=0.85`
- `OCR_MAX_TASKS_PER_PAGE=10`

---

## 14) Minimal Worker Pseudocode (OCR + Score)

```python
# 1) run ocrmypdf → searchable PDF + per-page PNG
# 2) for each page: tesseract → TSV
# 3) score = mean(conf where conf>=0)/100; text_coverage = total_token_area/page_area
# 4) low_conf spans: group adjacent tokens conf<80 → bbox union → hil_tasks

```

---

## 15) Security, Roles, Audit

- Roles: `uploader`, `reviewer`, `admin`. Only `reviewer` can resolve HIL tasks.
- Every HIL action → `audit_log` with payload hash; store original OCR text alongside corrections.
- Keep immutable copies of normalized PDFs; edits are overlays, never destructive changes.

---

## 16) Metrics & Ops

- **Throughput:** docs/hour per worker; **Backlog:** HIL tasks pending; **Yield:** % auto‑pass vs HIL.
- **Quality:** median `ocr_score`, % tables parsed, extraction precision on labeled test set.
- **Alarms:** HIL backlog > N, doc score trend down 3h, worker exceptions.

---

## 17) Test Plan (Week 1–2)

- Golden set of ~30 docs: native PDFs, low‑DPI scans, skewed, stamped, multi‑lang, tables.
- CI job runs end‑to‑end; asserts schema validity, element counts, ocr_score thresholds, table CSV existence.
- Manual HIL dry‑run with 10+ tasks to validate UI ergonomics and audit trail completeness.

---

## 18) Lane B (Future Hooks)

- **Advanced OCR:** MMOCR/LayoutLMv3 for complex layouts.
- **Table repair:** Camelot/Tabula fallback with heuristics.
- **Advanced IE:** LLM labeling with strict schemas + validator agent.
- **Storage:** Graph (Neo4j) + Vector (Qdrant) for clause‑level retrieval.

---

## 19) What’s In/Out for MVP

**In:** Upload → Normalize → OCR/Route → Partition → Heuristics → Contract JSON → Validators → HIL loop → Re‑emit.

**Out (deferred):** Supplemental uploads in HIL, auto‑table repair, clause labeling, multilingual beyond configured OCR langs.

---

## 20) Quick Start (dev)

1. `docker compose up -d` (db/minio/redis/api/worker)
2. Open MinIO console → create bucket `blobs`.
3. `POST /ingest` with a sample PDF. Watch logs for state transitions.
4. Visit HIL UI at `/review` → resolve tasks → confirm doc re‑emits with schema‑valid JSON.

> Simple, observable, auditable. Ship Lane A + HIL first; Lane B can bolt on later without breaking the contract.
>