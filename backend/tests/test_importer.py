import os
import threading
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.services.hashing import sha256_file
from app.services.importer import IntegrityCheckError, _copy_to_storage, import_source


def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_dedup_simple(db_session, tmp_path, storage_root):
    _write(tmp_path / "doc.txt", f"conteudo unico {uuid.uuid4()}")

    summary1 = import_source(db_session, str(tmp_path), storage_root, obra_wbs="PYTEST")
    assert summary1.total == 1
    assert summary1.novos == 1
    assert summary1.duplicados == 0

    summary2 = import_source(db_session, str(tmp_path), storage_root, obra_wbs="PYTEST")
    assert summary2.novos == 0
    assert summary2.duplicados == 1
    assert summary2.erros == []


def test_routing_by_extension(db_session, tmp_path, storage_root):
    _write(tmp_path / "a.txt", f"texto a {uuid.uuid4()}")
    _write(tmp_path / "b.csv", f"col1,col2\n{uuid.uuid4()}")

    summary = import_source(db_session, str(tmp_path), storage_root, obra_wbs="PYTEST")
    assert summary.novos == 2
    assert summary.sem_estante == 0

    items = db_session.execute(select(Item).where(Item.obra_wbs == "PYTEST")).scalars().all()
    estantes = sorted(item.estante for item in items)
    assert estantes == ["document_text", "structured_data"]


def test_unmapped_extension_is_flagged(db_session, tmp_path, storage_root):
    _write(tmp_path / f"arquivo_{uuid.uuid4().hex}.extensaoinexistente", "sem estante mapeada")

    summary = import_source(db_session, str(tmp_path), storage_root, obra_wbs="PYTEST")
    assert summary.novos == 0
    assert summary.sem_estante == 1


def test_text_file_gets_indexed_with_search_vector(db_session, tmp_path, storage_root):
    _write(tmp_path / "doc.txt", f"concreto armado estrutura {uuid.uuid4()}")

    import_source(db_session, str(tmp_path), storage_root, obra_wbs="PYTEST")

    item = db_session.execute(select(Item).where(Item.obra_wbs == "PYTEST")).scalar_one()
    assert item.status == "indexado"
    assert item.search_vector is not None


def test_copy_to_storage_happy_path(tmp_path, storage_root):
    src = tmp_path / "origem.txt"
    _write(src, f"conteudo legitimo {uuid.uuid4()}")
    hash_hex = sha256_file(str(src))

    dest_path = _copy_to_storage(str(src), storage_root, "document_text", hash_hex)

    assert os.path.exists(dest_path)
    assert sha256_file(dest_path) == hash_hex


def test_copy_to_storage_detects_pre_existing_corruption(tmp_path, storage_root):
    src = tmp_path / "origem.txt"
    _write(src, f"conteudo legitimo de origem {uuid.uuid4()}")
    hash_hex = sha256_file(str(src))

    dest_dir = os.path.join(storage_root, "document_text", hash_hex[:2])
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{hash_hex}.txt")
    _write(dest_path, "conteudo ERRADO colocado propositalmente")

    try:
        _copy_to_storage(str(src), storage_root, "document_text", hash_hex)
        assert False, "deveria ter levantado IntegrityCheckError"
    except IntegrityCheckError:
        pass

    assert not os.path.exists(dest_path)


def test_import_marks_item_as_falha_on_integrity_violation(db_session, tmp_path, storage_root):
    src_dir = tmp_path / "corrompido"
    src_dir.mkdir()
    src = src_dir / "doc.txt"
    _write(src, f"conteudo legitimo original {uuid.uuid4()}")

    hash_hex = sha256_file(str(src))
    dest_dir = os.path.join(storage_root, "document_text", hash_hex[:2])
    os.makedirs(dest_dir, exist_ok=True)
    _write(os.path.join(dest_dir, f"{hash_hex}.txt"), "conteudo ERRADO")

    summary = import_source(db_session, str(src_dir), storage_root, obra_wbs="PYTEST")

    assert summary.novos == 0
    assert len(summary.erros) == 1
    assert "falha de integridade" in summary.erros[0]

    item = db_session.execute(select(Item).where(Item.hash_sha256 == hash_hex)).scalar_one()
    assert item.status == "falha_processamento"


def test_concurrent_import_same_hash_yields_one_novo_one_duplicado(tmp_path, storage_root, db_engine):
    """Reproduz o teste de concorrencia exigido em docs/S6-testes.md: duas
    importacoes simultaneas do mesmo arquivo novo devem resultar em exatamente
    1 novo + 1 duplicado, sem nenhum erro.

    Usa duas conexoes/transacoes reais e independentes (nao a fixture
    db_session, que e uma unica transacao) para de fato reproduzir a corrida.
    As linhas geradas ficam no banco real, marcadas com obra_wbs='PYTEST_CONC'
    e conteudo unico por execucao — aceitavel dado o desenho Zero Exclusao
    (P3) do sistema, que nao permite apagar linhas de items/custody_log.
    """
    src_dir = tmp_path / "concorrencia"
    src_dir.mkdir()
    _write(src_dir / "unico.txt", f"conteudo unico para teste de concorrencia real {uuid.uuid4()}")

    results = []

    def worker():
        with Session(db_engine, future=True) as session:
            summary = import_source(session, str(src_dir), storage_root, obra_wbs="PYTEST_CONC")
            results.append(summary)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 2
    total_novos = sum(r.novos for r in results)
    total_duplicados = sum(r.duplicados for r in results)
    total_erros = sum(len(r.erros) for r in results)

    assert total_novos == 1
    assert total_duplicados == 1
    assert total_erros == 0
