import os
import shutil
from dataclasses import dataclass, field
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Item
from app.services.cota import generate_cota
from app.services.custody import log_event
from app.services.estante_router import route
from app.services.extraction import extract_text
from app.services.hashing import sha256_file

ACTOR = "importer_v0"

STATUS_RECEBIDO = "recebido"
STATUS_ROTEADO = "roteado"
STATUS_PROCESSANDO = "processando"
STATUS_PROCESSADO = "processado"
STATUS_INDEXADO = "indexado"
STATUS_FALHA = "falha_processamento"


@dataclass
class ImportSummary:
    total: int = 0
    novos: int = 0
    duplicados: int = 0
    indexados: int = 0
    sem_texto: int = 0
    sem_estante: int = 0
    erros: List[str] = field(default_factory=list)


def _copy_to_storage(source_path: str, storage_root: str, estante: str, hash_hex: str) -> str:
    ext = os.path.splitext(source_path)[1].lower()
    dest_dir = os.path.join(storage_root, estante, hash_hex[:2])
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{hash_hex}{ext}")
    if not os.path.exists(dest_path):
        shutil.copy2(source_path, dest_path)
    return dest_path


def _import_file(session: Session, file_path: str, storage_root: str, obra_wbs: str, summary: ImportSummary) -> None:
    hash_hex = sha256_file(file_path)

    existing = session.execute(select(Item).where(Item.hash_sha256 == hash_hex)).scalar_one_or_none()
    if existing is not None:
        log_event(session, existing.id, "deduplicacao", ACTOR, hash_hex, reason=f"origem_repetida:{file_path}")
        summary.duplicados += 1
        return

    filename = os.path.basename(file_path)
    estante = route(filename)

    item = Item(hash_sha256=hash_hex, storage_path="", status=STATUS_RECEBIDO, estante=None, obra_wbs=obra_wbs)
    session.add(item)
    session.flush()
    log_event(session, item.id, "recebimento", ACTOR, hash_hex, reason=f"origem:{file_path}")

    if estante is None:
        log_event(session, item.id, "alerta_integridade", ACTOR, hash_hex, reason=f"extensao_nao_mapeada:{filename}")
        summary.sem_estante += 1
        session.flush()
        return

    item.estante = estante
    item.cota = generate_cota(session, estante, obra_wbs, hash_hex)
    item.status = STATUS_ROTEADO
    log_event(session, item.id, "roteamento", ACTOR, hash_hex, reason=f"estante:{estante}")

    item.storage_path = _copy_to_storage(file_path, storage_root, estante, hash_hex)

    item.status = STATUS_PROCESSANDO
    text = None
    try:
        text = extract_text(file_path, estante)
    except Exception as exc:
        log_event(session, item.id, "processamento", ACTOR, hash_hex, reason=f"extracao_falhou:{exc}")

    if text:
        item.search_vector = func.to_tsvector("portuguese", text)
        item.status = STATUS_INDEXADO
        log_event(session, item.id, "indexacao", ACTOR, hash_hex)
        summary.indexados += 1
    else:
        item.status = STATUS_PROCESSADO
        log_event(session, item.id, "processamento", ACTOR, hash_hex, reason="sem_texto_extraido")
        summary.sem_texto += 1

    item.processed_at = func.now()
    summary.novos += 1


def import_source(session: Session, source_dir: str, storage_root: str, obra_wbs: str = "INDEFINIDO") -> ImportSummary:
    summary = ImportSummary()
    for root, _dirs, files in os.walk(source_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            summary.total += 1
            try:
                _import_file(session, file_path, storage_root, obra_wbs, summary)
                session.commit()
            except Exception as exc:
                session.rollback()
                summary.erros.append(f"{file_path}: {exc}")
    return summary
