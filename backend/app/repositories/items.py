from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Item


def get_item_by_cota(session: Session, cota: str) -> Optional[Item]:
    return session.execute(select(Item).where(Item.cota == cota)).scalar_one_or_none()


def search_items(session: Session, query: str, limit: int) -> List[Tuple[Item, float]]:
    tsquery = func.plainto_tsquery("portuguese", query)
    rank = func.ts_rank(Item.search_vector, tsquery).label("rank")
    stmt = (
        select(Item, rank)
        .where(Item.search_vector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).all())
