import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Item
from app.services.cota import generate_cota
from app.services.custody import log_event
from app.services.estante_router import route
from app.services.extraction import extract_text
from app.services.hashing import sha256_file
from app.services.hudson_desbloqueador import HudsonDesbloqueador

ACTOR = "importer_v2"

STATUS_RECEBIDO = "recebido"
STATUS_ROTEADO = "roteado"
STATUS_PROCESSANDO = "processando"
STATUS_PROCESSADO = "processado"
STATUS_INDEXADO = "indexado"
STATUS_FALHA = "falha_processamento"


class IntegrityCheckError(Exception):
    """Levantado quando a copia em custodia nao bate com o hash de origem."""


@dataclass
class ImportSummary:
    ronda_id: Optional[str] = None
    total: int = 0
    novos: int = 0
    duplicados: int = 0
    indexados: int = 0
    sem_texto: int = 0
    sem_estante: int = 0
    desbloqueados: int = 0
    erros: List[str] = field(default_factory=list)


def _find_existing(session: Session, hash_hex: str) -> Optional[Item]:
    return session.execute(select(Item).where(Item.hash_sha256 == hash_hex)).scalar_one_or_none()


def _copy_to_storage(source_path: str, storage_root: str, estante: str, hash_hex: str) -> str:
    ext = os.path.splitext(source_path)[1].lower()
    dest_dir = os.path.join(storage_root, estante, hash_hex[:2])
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{hash_hex}{ext}")
    if not os.path.exists(dest_path):
        shutil.copy2(source_path, dest_path)
    if sha256_file(dest_path) != hash_hex:
        os.remove(dest_path)
        raise IntegrityCheckError(f"hash da copia em {dest_path} nao confere com a origem")
    return dest_path


def _import_file(
    session: Session,
    file_path: str,
    storage_root: str,
    obra_wbs: str,
    summary: ImportSummary,
    ronda_id: Optional[str] = None,
    usuario_captura: str = "sistema",
) -> None:
    hash_hex = sha256_file(file_path)

    # 1. Metadados de Origem do Sistema Operacional
    stat = os.stat(file_path)
    nome_arquivo = os.path.basename(file_path)
    caminho_orig = os.path.abspath(file_path)
    extensao_orig = os.path.splitext(file_path)[1].lower()
    tamanho_bytes = stat.st_size
    mtime_orig = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    # 2. Deduplicacao estrita
    existing = _find_existing(session, hash_hex)
    if existing is not None:
        log_event(session, existing.id, "deduplicacao", ACTOR, hash_hex, reason=f"origem_repetida:{file_path}")
        summary.duplicados += 1
        return

    estante = route(nome_arquivo)

    # 3. Criacao do Item com Metadados Completos
    item = Item(
        hash_sha256=hash_hex,
        storage_path="",
        status=STATUS_RECEBIDO,
        estante=None,
        obra_wbs=obra_wbs,
        nome_arquivo_original=nome_arquivo,
        caminho_origem=caminho_orig,
        extensao_original=extensao_orig,
        tamanho_bytes=tamanho_bytes,
        mtime_origem=mtime_orig,
        ronda_id=ronda_id,
        usuario_captura=usuario_captura,
        status_desbloqueio="original",
    )
    session.add(item)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        existing = _find_existing(session, hash_hex)
        if existing is None:
            raise
        log_event(
            session, existing.id, "deduplicacao", ACTOR, hash_hex, reason=f"origem_repetida_concorrente:{file_path}"
        )
        summary.duplicados += 1
        return

    log_event(session, item.id, "recebimento", ACTOR, hash_hex, reason=f"origem:{file_path}")

    if estante is None:
        log_event(session, item.id, "alerta_integridade", ACTOR, hash_hex, reason=f"extensao_nao_mapeada:{nome_arquivo}")
        summary.sem_estante += 1
        session.flush()
        return

    item.estante = estante
    item.cota = generate_cota(session, estante, obra_wbs, hash_hex)
    item.status = STATUS_ROTEADO
    log_event(session, item.id, "roteamento", ACTOR, hash_hex, reason=f"estante:{estante}")

    # 4. Copia para Storage Seguro
    try:
        item.storage_path = _copy_to_storage(file_path, storage_root, estante, hash_hex)
    except IntegrityCheckError as exc:
        item.status = STATUS_FALHA
        log_event(session, item.id, "alerta_integridade", ACTOR, hash_hex, reason=f"copia_corrompida:{exc}")
        summary.erros.append(f"{file_path}: falha de integridade na copia em custodia - {exc}")
        return

    # 5. Desbloqueador Forense (se protegido ou compactado)
    caminho_para_extracao = file_path
    if extensao_orig in [".pdf", ".docx", ".xlsx", ".zip", ".rar", ".7z"]:
        try:
            desb = HudsonDesbloqueador()
            res_desb = desb.desbloquear_arquivo(file_path)
            if isinstance(res_desb, str) and os.path.exists(res_desb) and res_desb != file_path:
                caminho_para_extracao = res_desb
                item.status_desbloqueio = "desbloqueado"
                item.metodo_desbloqueio = "hudson_desbloqueador"
                log_event(session, item.id, "liberacao", ACTOR, hash_hex, reason=f"desbloqueado:{res_desb}")
                summary.desbloqueados += 1
        except Exception as desb_err:
            item.status_desbloqueio = "falha_desbloqueio"
            log_event(session, item.id, "alerta_integridade", ACTOR, hash_hex, reason=f"erro_desbloqueio:{desb_err}")

    # 6. Extracao de Texto e Indexacao Full-Text
    item.status = STATUS_PROCESSANDO
    text = None
    try:
        text = extract_text(caminho_para_extracao, estante)
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


def import_source(
    session: Session,
    source_dir: str,
    storage_root: str,
    obra_wbs: str = "INDEFINIDO",
    ronda_id: Optional[str] = None,
    usuario_captura: str = "sistema",
) -> ImportSummary:
    if ronda_id is None:
        ronda_id = f"RONDA-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    summary = ImportSummary(ronda_id=ronda_id)
    for root, _dirs, files in os.walk(source_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            summary.total += 1
            try:
                _import_file(
                    session,
                    file_path,
                    storage_root,
                    obra_wbs,
                    summary,
                    ronda_id=ronda_id,
                    usuario_captura=usuario_captura,
                )
                session.commit()
            except Exception as exc:
                session.rollback()
                summary.erros.append(f"{file_path}: {exc}")
    return summary
