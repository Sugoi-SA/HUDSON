from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item

MIN_HASH_LEN = 8
MAX_HASH_LEN = 64


def generate_cota(session: Session, estante: str, obra_wbs: str, hash_hex: str) -> str:
    year = datetime.now(timezone.utc).year
    hash_len = MIN_HASH_LEN
    while hash_len <= MAX_HASH_LEN:
        candidate = f"{estante}-{obra_wbs}-{year}-{hash_hex[:hash_len]}"
        exists = session.execute(select(Item.id).where(Item.cota == candidate)).first()
        if exists is None:
            return candidate
        hash_len += 2
    raise RuntimeError(f"Nao foi possivel gerar cota unica para hash {hash_hex}")
