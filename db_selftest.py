# db_selftest.py
import os, uuid, json, datetime as dt
from fastapi import APIRouter, HTTPException, Depends, Request
import asyncpg

router = APIRouter(prefix="/admin")

SELF_TEST_TOKEN = os.getenv("SELF_TEST_TOKEN", "changeme")

async def get_conn():
    dsn = os.environ["DATABASE_URL"]
    return await asyncpg.connect(dsn)

@router.get("/db-health")
async def db_health():
    conn = await get_conn()
    try:
        row = await conn.fetchrow(
            "select current_database() db, current_user usr, now() at time zone 'utc' as now_utc"
        )
        # lightweight table presence check
        tables = await conn.fetch(
            """select table_name from information_schema.tables
               where table_schema='public' and table_name in
               ('documents','obligations','obligation_evidence_links')"""
        )
        return {"ok": True, **dict(row), "tables": [r["table_name"] for r in tables]}
    finally:
        await conn.close()

@router.post("/db-self-test")
async def db_self_test(request: Request):
    token = request.query_params.get("token")
    if token != SELF_TEST_TOKEN:
        raise HTTPException(status_code=401, detail="bad token")

    conn = await get_conn()
    results = {"ok": False, "steps": []}
    try:
        tr = conn.transaction()
        await tr.start()

        # 1) Insert a test document
        doc_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO documents (document_id, contract_type, contract_name, effective_date,
                                      extracted_fields, created_at)
               VALUES ($1,$2,$3,CURRENT_DATE,$4,NOW())""",
            doc_id, "Unknown", "SELFTEST_DOC", json.dumps({}),  # serialize to JSON string
        )
        results["steps"].append({"insert_document": "INSERT 0 1", "doc_id": doc_id})

        # 2) apply_extraction idempotency (UPSERT on (document_id, obligation_hash))
        payload = {
            "extracted_fields": {"doc_type_guess": "PSA"},
            "obligations": [{
                "obligation_type": "make_payment",
                "status": "open",
                "trigger_event": "Close of Escrow",
                "due_date": (dt.date.today() + dt.timedelta(days=30)).isoformat(),
                "responsible_party": "Buyer",
                "description": "Pay transfer tax at recording",
                "evidence": [{"page_from": 7, "page_to": 7, "note": "§7.3"}]
            }]
        }
        await conn.fetchval("SELECT apply_extraction($1, $2::jsonb, true)", doc_id, json.dumps(payload))
        await conn.fetchval("SELECT apply_extraction($1, $2::jsonb, true)", doc_id, json.dumps(payload))  # run twice

        dup_cnt = await conn.fetchval("""
            WITH d AS (
              SELECT obligation_hash, COUNT(*) c
              FROM obligations WHERE document_id = $1 GROUP BY 1
            )
            SELECT COALESCE(MAX(c),0) FROM d;""", doc_id)
        results["steps"].append({"apply_extraction_idempotent": (dup_cnt == 1), "max_duplicates": dup_cnt})

        # 3) evidence de-dup (note excluded from unique key)
        # try to insert same link with a different note -> should remain 1 row
        await conn.execute("""
            INSERT INTO obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to, note)
            SELECT o.obligation_id, $1::uuid, 7, 7, 'different note'
            FROM obligations o WHERE o.document_id=$1 LIMIT 1
            ON CONFLICT (obligation_id, evidence_document_id, page_from, page_to) DO NOTHING;
        """, doc_id)
        ev_dups = await conn.fetchval("""
            SELECT COUNT(*) FROM obligation_evidence_links e
            JOIN obligations o ON o.obligation_id=e.obligation_id
            WHERE o.document_id=$1 AND e.page_from=7 AND e.page_to=7;""", doc_id)
        results["steps"].append({"evidence_unique": (ev_dups == 1), "rows": ev_dups})

        # 4) obligations_due_60 view exists & returns the test row
        due_rows = await conn.fetch("""
            SELECT 1 FROM obligations_due_60 WHERE document_id=$1 LIMIT 1;
        """, doc_id)
        results["steps"].append({"obligations_due_60_ok": bool(due_rows)})

        # rollback so the DB stays clean
        await tr.rollback()
        results["ok"] = True
        return results
    except Exception as e:
        try:
            await tr.rollback()
        except Exception:
            pass
        results["error"] = str(e)
        return results
    finally:
        await conn.close()