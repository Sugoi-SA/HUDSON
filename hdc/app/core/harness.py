"""
==============================================================================
🛡️ MÓDULO HARNESS & RAPIDFUZZ DO HUDSON DC (HDC)
Sistema de Proteção, Guardrails Anti-Alucinação e Confiança Zero
==============================================================================
Responsável por garantir que a IA e os modelos generativos NÃO traiam a confiança
do sistema corporativo, forçando aterramento (grounding) factual absoluto,
tolerância fonética/ortográfica com RapidFuzz e travas determinísticas de SoD.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("hdc.core.harness")

# Tentativa de importar RapidFuzz; se não disponível, utiliza fallback nativo difflib
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    import difflib
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("RapidFuzz não instalado localmente. Utilizando fallback nativo difflib.")


# ==============================================================================
# 🎯 1. MOTOR RAPIDFUZZ COM THRESHOLD RÍGIDO (Anti-Alucinação)
# ==============================================================================
def calcular_similaridade_fuzzy(termo_busca: str, candidato: str) -> float:
    """
    Calcula o score de similaridade entre 0.0 e 100.0.
    Utiliza token_set_ratio do RapidFuzz (tolerante a ordem de palavras e acentos)
    ou difflib.SequenceMatcher em caso de fallback.
    """
    termo = termo_busca.strip().lower()
    alvo = candidato.strip().lower()

    if not termo or not alvo:
        return 0.0

    if termo == alvo:
        return 100.0

    # Se uma for substring exata da outra, pontuação alta
    if termo in alvo or alvo in termo:
        return 90.0

    if RAPIDFUZZ_AVAILABLE:
        # RapidFuzz token_set_ratio trata nomes como "Akagui, Ronaldo" e "Ronaldo Akaguy"
        return float(fuzz.token_set_ratio(termo, alvo))
    else:
        # Fallback difflib
        matcher = difflib.SequenceMatcher(None, termo, alvo)
        return float(matcher.ratio() * 100.0)


class RAGHarnessGuard:
    """
    Anel de Contenção de RAG e Busca Factual.
    Impede que o sistema responda com base em inferências generativas ou suposições.
    """
    LIMIAR_MINIMO_CONFIANCA: float = 75.0  # Menos que 75% é rejeitado categoricamente

    @classmethod
    def buscar_entidade_ancorada(
        cls,
        termo: str,
        catalogo_entidades: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """
        Executa busca factual contra base verificada.
        Retorna (encontrado, entidade, score_confianca).
        Se nenhum candidato atingir o limiar seguro, devolve False e None.
        A IA é expressamente proibida de preencher lacunas.
        """
        melhor_candidato = None
        maior_score = 0.0

        for item in catalogo_entidades:
            nome = item.get("nome", "")
            departamento = item.get("departamento", "")
            
            # Testa nome principal e variações/departamentos
            score_nome = calcular_similaridade_fuzzy(termo, nome)
            score_dep = calcular_similaridade_fuzzy(termo, departamento)
            score_item = max(score_nome, score_dep)

            if score_item > maior_score:
                maior_score = score_item
                melhor_candidato = item

        if maior_score >= cls.LIMIAR_MINIMO_CONFIANCA and melhor_candidato:
            logger.info(f"[HARNESS RAG] Entidade '{melhor_candidato.get('nome')}' validada com confiança {maior_score:.1f}%")
            return True, melhor_candidato, maior_score

        logger.warning(f"[HARNESS RAG] Termo '{termo}' não atingiu limiar seguro (maior score: {maior_score:.1f}% < {cls.LIMIAR_MINIMO_CONFIANCA}%). Retornando NÃO ENCONTRADO.")
        return False, None, maior_score


# ==============================================================================
# 🛡️ 2. GUARDA DE SEGREGAÇÃO DE FUNÇÕES (SoD Guard)
# ==============================================================================
def validar_segregacao_funcoes_sod(maker: str, checker: str, sod_validado: bool) -> Tuple[bool, Optional[str]]:
    """
    Garante que as regras de controle interno nunca sejam violadas:
    - Maker não pode ser igual a Checker (auto-aprovação é fraude).
    - O flag sod_validado deve ter sido atestado pelo Cofre PAM.
    """
    maker_norm = maker.strip().lower()
    checker_norm = checker.strip().lower()

    if maker_norm == checker_norm:
        return False, "Violação de SoD: Maker e Checker não podem ser o mesmo usuário (auto-aprovação proibida)."

    if not sod_validado:
        return False, "Violação de SoD: O processo não foi previamente validado e certificado pelo Cofre PAM."

    return True, None
