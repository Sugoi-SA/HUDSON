from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# 🔹 Evento 1: Notificação de Anfitrião (Tab 2 Front-End DAI)
# --------------------------------------------------------------------------
class VisitanteInfo(BaseModel):
    id_usuario: Optional[int] = None
    nome: str
    perfil_pam: str = "visitante"
    unidades_autorizadas: List[str] = Field(default_factory=list)


class AnfitriaoAlvoInfo(BaseModel):
    canal_preferencial: str = "slack_and_push"
    mensagem: str


class NotificarAnfitriaoRequest(BaseModel):
    evento: str = "DAI_NOTIFICAR_ANFITRIAO"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ticket_id: str
    sala_destino: str
    departamento: str
    visitante: VisitanteInfo
    anfitriao_alvo: AnfitriaoAlvoInfo


class NotificarAnfitriaoResponse(BaseModel):
    status: str = "ACCEPTED"
    id_despacho: str
    canais_acionados: List[str]
    tempo_estimado_entrega: str = "< 2s"


# --------------------------------------------------------------------------
# 🔹 Evento 2: Quarentena e Auditoria de Documento / CCB (Esteira PAM & Kan-sa)
# --------------------------------------------------------------------------
class QuarentenaAuditoriaRequest(BaseModel):
    evento: str = "DAI_QUARENTENA_SUBMETIDA"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hash_documento: str
    status_parecer: str = "APROVADO"
    maker: str
    checker: str
    sod_validado: bool = True
    metadados: Dict[str, Any] = Field(default_factory=dict)
    destino_kansa: str = "esteira_pericial_automatica"


class QuarentenaAuditoriaResponse(BaseModel):
    status: str = "ACCEPTED"
    protocolo_auditoria: str
    esteira_acionada: str
    mensagem: str = "Ordem pericial encaminhada com sucesso para o KAN-SA."


# --------------------------------------------------------------------------
# 🔹 Evento 3: Alerta de Emergência P1 (Dr. SaulLM / Jurídico)
# --------------------------------------------------------------------------
class AlertaEmergenciaRequest(BaseModel):
    evento: str = "ALERTA_EMERGENCIA_P1"
    nivel_prioridade: str = "P1_CRITICO"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ticket_id: str
    descricao: str
    localizacao: str = "Lobby Principal"
    acao_imediata: str


class AlertaEmergenciaResponse(BaseModel):
    status: str = "SIRENE_DISPARADA"
    alerta_id: str
    autoridades_acionadas: List[str]
    diretriz_saullm: Optional[str] = None


# --------------------------------------------------------------------------
# 🔹 Evento 4: Consulta Semântica ao Grafo Corporativo
# --------------------------------------------------------------------------
class EntidadeGrafo(BaseModel):
    nome: str
    cargo: str
    departamento: str
    grau_risco: str = "BAIXO"
    relacionamentos_ativos: List[str] = Field(default_factory=list)


class ConsultaGrafoResponse(BaseModel):
    encontrado: bool
    entidade: Optional[EntidadeGrafo] = None


# --------------------------------------------------------------------------
# 🔹 Callback de Retorno do HUDSON DC para a DAI
# --------------------------------------------------------------------------
class HudsonCallbackDAI(BaseModel):
    id_evento_origem: str
    ticket_id: str
    tipo_retorno: str  # ex: ANFITRIAO_RESPONDEU, LAUDO_KANSA_CONCLUIDO
    status: str        # ex: AUTORIZADO, REJEITADO, CONFORME
    resposta_anfitriao: Optional[str] = None
    catraca_liberada: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
