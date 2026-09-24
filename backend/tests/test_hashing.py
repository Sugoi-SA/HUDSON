import hashlib

from app.services.hashing import sha256_file


def test_sha256_file_matches_hashlib(tmp_path):
    p = tmp_path / "arquivo.txt"
    p.write_text("conteudo de teste para hashing", encoding="utf-8")

    expected = hashlib.sha256(p.read_bytes()).hexdigest()

    assert sha256_file(str(p)) == expected


def test_sha256_file_is_deterministic(tmp_path):
    p = tmp_path / "arquivo.txt"
    p.write_text("mesmo conteudo", encoding="utf-8")

    assert sha256_file(str(p)) == sha256_file(str(p))
