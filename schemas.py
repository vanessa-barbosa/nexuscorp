# schemas.py - Contratos de entrada e saida da API (Pydantic)
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List
from models import PerfilUsuario, CategoriaDespesa, SituacaoSolicitacao

# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Usuario (Bloco 2) ---
class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(..., min_length=6)

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    departamento_id: int
    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    senha: Optional[str] = Field(None, min_length=6)

# --- Historico (Bloco 3) ---
# HistoricoResponse: o que volta no historico - mostra quem decidiu e quando (RN12)
class HistoricoResponse(BaseModel):
    id: int
    etapa: str
    decisao: str
    observacao: Optional[str] = None
    responsavel_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# --- Solicitacao / Reembolso (Bloco 3) ---
# SolicitacaoCreate: o que o colaborador manda para criar
# NOTE: sem solicitante_id, sem situacao - o backend define (evita falsificar dono/status)
class SolicitacaoCreate(BaseModel):
    categoria: CategoriaDespesa
    valor: float = Field(..., gt=0)  # RN04: Pydantic ja barra <= 0
    data_despesa: date  # RN06: validado na rota (nao pode ser futura)
    justificativa: str = Field(..., min_length=3)
    referencia_comprovante: str = Field(..., min_length=1, max_length=150)

# SolicitacaoUpdate: editar em rascunho - mesmos campos, todos opcionais
# NOTE: sem situacao, sem solicitante_id - nao da para trocar dono/status por aqui (RN07)
class SolicitacaoUpdate(BaseModel):
    categoria: Optional[CategoriaDespesa] = None
    valor: Optional[float] = Field(None, gt=0)  # RN04 de novo
    data_despesa: Optional[date] = None
    justificativa: Optional[str] = Field(None, min_length=3)
    referencia_comprovante: Optional[str] = Field(None, min_length=1, max_length=150)

# SolicitacaoResponse: o que a API devolve - completo, com historico junto
class SolicitacaoResponse(BaseModel):
    id: int
    solicitante_id: int
    categoria: CategoriaDespesa
    valor: float
    data_despesa: date
    justificativa: str
    referencia_comprovante: str
    situacao: SituacaoSolicitacao
    created_at: Optional[datetime] = None
    historico: List[HistoricoResponse] = []
    class Config:
        from_attributes = True


# --- Decisao de aprovacao (Bloco 4) ---
# DecisaoRequest: o que gestor/financeiro mandam para decidir
# observacao = obrigatoria na recusa (RN11), opcional na aprovacao
class DecisaoRequest(BaseModel):
    observacao: Optional[str] = Field(None, max_length=500)
