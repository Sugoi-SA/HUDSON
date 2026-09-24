from fastapi import APIRouter, HTTPException

from app.db import get_session
from app.repositories.items import get_item_by_cota
from app.schemas.items import ItemOut
from app.services.custody import log_event

router = APIRouter()

ACTOR = "api_v0"


@router.get("/items/{cota}", response_model=ItemOut)
def get_item(cota: str):
    with get_session() as session:
        item = get_item_by_cota(session, cota)
        if item is None:
            raise HTTPException(status_code=404, detail="Item nao encontrado")

        log_event(session, item.id, "consulta", ACTOR, item.hash_sha256, reason=f"lookup_cota:{cota}")

        return ItemOut.model_validate(item)
