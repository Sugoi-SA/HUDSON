import uuid

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
    estante: Mapped[str | None] = mapped_column(ForeignKey("hudson.estant_types.codigo"), nullable=True)
    cota: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    obra_wbs: Mapped[str | None] = mapped_column(String, nullable=True)
    duplicate_of_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hudson.items.id"), nullable=True
    )
    received_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_vector: Mapped[object | None] = mapped_column(TSVECTOR, nullable=True)


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
    item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hudson.items.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
