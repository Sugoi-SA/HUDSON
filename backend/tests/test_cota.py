from datetime import datetime, timezone

from app.services.cota import generate_cota


def test_generate_cota_format(db_session):
    hash_hex = "abcd1234efgh5678" + "0" * 48
    cota = generate_cota(db_session, "document_text", "OBRATESTE", hash_hex)

    year = datetime.now(timezone.utc).year
    assert cota == f"document_text-OBRATESTE-{year}-{hash_hex[:8]}"


def test_generate_cota_is_unique_per_hash(db_session):
    hash_a = "a" * 64
    hash_b = "b" * 64

    cota_a = generate_cota(db_session, "document_text", "OBRATESTE", hash_a)
    cota_b = generate_cota(db_session, "document_text", "OBRATESTE", hash_b)

    assert cota_a != cota_b
