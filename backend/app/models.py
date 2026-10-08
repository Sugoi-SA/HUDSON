import uuid
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EstantType(Base):
    __tablename__ = "estant_types"
    __table_args__ = {"schema": "hudson"}

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    descricao: Mapped[str] = mapped_column(String, nullable=False)


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": "hudson"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    hash_sha256: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    estante: Mapped[Optional[str]] = mapped_column(ForeignKey("hudson.estant_types.codigo"), nullable=True)
    cota: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    obra_wbs: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duplicate_of_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hudson.items.id"), nullable=True
    )
    received_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    search_vector: Mapped[Optional[object]] = mapped_column(TSVECTOR, nullable=True)

    # Metadados de Origem e Rastreamento de Ronda (v2.0)
    nome_arquivo_original: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caminho_origem: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extensao_original: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tamanho_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mtime_origem: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    ronda_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    usuario_captura: Mapped[Optional[str]] = mapped_column(String(255), server_default="sistema", nullable=True)
    maquina_origem: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_desbloqueio: Mapped[Optional[str]] = mapped_column(String(50), server_default="original", nullable=True)
    metodo_desbloqueio: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class CustodyLog(Base):
    __tablename__ = "custody_log"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('recebimento', 'retencao', 'liberacao', 'deduplicacao', "
            "'roteamento', 'processamento', 'falha_llm', 'reprocessamento', "
            "'indexacao', 'lock_custodia', 'consulta', 'alerta_integridade')"
        ),
        {"schema": "hudson"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hudson.items.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
