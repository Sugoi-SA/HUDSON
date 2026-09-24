import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(DATABASE_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Sessao de teste ligada a uma transacao externa que e sempre revertida
    no final, mesmo que o codigo de producao chame session.commit() (usa
    savepoints). Isso permite exercitar o pipeline real (hash/dedup/roteamento/
    triggers) contra o Postgres de verdade sem deixar lixo permanente no
    acervo, que e append-only por desenho (P3 - Zero Exclusao)."""
    connection = db_engine.connect()
    outer_transaction = connection.begin()

    session_factory = sessionmaker(bind=connection, future=True)
    session = session_factory()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def storage_root(tmp_path_factory):
    """Diretorio de custodia isolado do `tmp_path` de cada teste. Precisa
    viver fora da arvore usada como pasta de origem, senao import_source
    (que varre recursivamente) reimporta as proprias copias que acabou de
    gravar."""
    return str(tmp_path_factory.mktemp("storage"))
