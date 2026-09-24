from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cota: Optional[str]
    hash_sha256: str
    estante: Optional[str]
    status: str
    storage_path: str
    obra_wbs: Optional[str]
    received_at: datetime
    processed_at: Optional[datetime]


class SearchResultItem(BaseModel):
    cota: Optional[str]
    estante: Optional[str]
    status: str
    storage_path: str
    received_at: datetime
    rank: float


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]
