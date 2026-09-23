from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import func, select

from app.custody import log_event
from app.db import get_session
from app.models import Item

app = FastAPI(title="HUDSON S1 - API v0")

ACTOR = "api_v0"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
def search(q: str = Query(..., min_length=2), limit: int = Query(50, le=200)):
    tsquery = func.plainto_tsquery("portuguese", q)
    rank = func.ts_rank(Item.search_vector, tsquery).label("rank")
    stmt = (
        select(Item, rank)
        .where(Item.search_vector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(limit)
    )

    with get_session() as session:
        rows = session.execute(stmt).all()
        results = [
            {
                "cota": item.cota,
                "estante": item.estante,
                "status": item.status,
                "storage_path": item.storage_path,
                "received_at": item.received_at,
                "rank": float(rank_value),
            }
            for item, rank_value in rows
        ]
        log_event(session, None, "consulta", ACTOR, "n/a", reason=f"busca:{q}")

    return {"query": q, "total": len(results), "results": results}


@app.get("/items/{cota}")
def get_item(cota: str):
    with get_session() as session:
        item = session.execute(select(Item).where(Item.cota == cota)).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="Item nao encontrado")

        log_event(session, item.id, "consulta", ACTOR, item.hash_sha256, reason=f"lookup_cota:{cota}")

        return {
            "cota": item.cota,
            "hash_sha256": item.hash_sha256,
            "estante": item.estante,
            "status": item.status,
            "storage_path": item.storage_path,
            "obra_wbs": item.obra_wbs,
            "received_at": item.received_at,
            "processed_at": item.processed_at,
        }
