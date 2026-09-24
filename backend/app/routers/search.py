from fastapi import APIRouter, Query

from app.db import get_session
from app.repositories.items import search_items
from app.schemas.items import SearchResponse, SearchResultItem
from app.services.custody import log_event

router = APIRouter()

ACTOR = "api_v0"


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=2), limit: int = Query(50, le=200)):
    with get_session() as session:
        rows = search_items(session, q, limit)
        results = [
            SearchResultItem(
                cota=item.cota,
                estante=item.estante,
                status=item.status,
                storage_path=item.storage_path,
                received_at=item.received_at,
                rank=float(rank_value),
            )
            for item, rank_value in rows
        ]
        log_event(session, None, "consulta", ACTOR, "n/a", reason=f"busca:{q}")

    return SearchResponse(query=q, total=len(results), results=results)
