from app.services.estante_router import route


def test_route_maps_known_extensions():
    assert route("contrato.pdf") == "document_text"
    assert route("foto.jpg") == "image"
    assert route("planilha.xlsx") == "structured_data"
    assert route("desenho.dwg") == "engineering_drawings"
    assert route("gravacao.mp3") == "audio_video"
    assert route("email.eml") == "communication"


def test_route_unknown_extension_returns_none():
    assert route("arquivo.extensao_inexistente") is None


def test_route_is_case_insensitive():
    assert route("CONTRATO.PDF") == "document_text"
