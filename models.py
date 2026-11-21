# models.py - Tabelas do banco (o que vira tabela no SQLite)
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

# --- Enums: valores fixos permitidos ---

# Perfil de utilizacao: quem pode fazer o que no sistema
class PerfilUsuario(str, enum.Enum):
    COLABORADOR = "colaborador"
    GESTOR = "gestor"
    FINANCEIRO = "financeiro"

# Categoria da despesa: tipo do gasto
class CategoriaDespesa(str, enum.Enum):
    ALIMENTACAO = "alimentacao"
    TRANSPORTE = "transporte"
    HOSPEDAGEM = "hospedagem"
    MATERIAIS = "materiais"

# Situacao: onde a solicitacao esta no fluxo de aprovacao
class SituacaoSolicitacao(str, enum.Enum):
    RASCUNHO = "rascunho"
    AGUARDANDO_GESTOR = "aguardando_gestor"
    AGUARDANDO_FINANCEIRO = "aguardando_financeiro"
    APROVADA = "aprovada"
    PAGA = "paga"
    RECUSADA = "recusada"

# --- Tabelas ---

class Departamento(Base):
    __tablename__ = "departamentos"  # nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True)  # PK, auto-incremento
    nome = Column(String(100), unique=True, nullable=False)  # nome unico, obrigatorio

    # Relacao reversa: um departamento tem varios usuarios
    usuarios = relationship("Usuario", back_populates="departamento")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)  # login, unico
    senha_hash = Column(String(255), nullable=False)  # NUNCA senha pura, so hash (RN13)
    perfil = Column(SAEnum(PerfilUsuario), nullable=False, default=PerfilUsuario.COLABORADOR)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=False)

    # Relacoes: usuario pertence a um departamento, tem varias solicitacoes
    departamento = relationship("Departamento", back_populates="usuarios")
    solicitacoes = relationship("Solicitacao", back_populates="solicitante", foreign_keys="Solicitacao.solicitante_id")

class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)  # quem pediu
    categoria = Column(SAEnum(CategoriaDespesa), nullable=False)
    valor = Column(Float, nullable=False)  # RN04: > 0, validado na API
    data_despesa = Column(Date, nullable=False)  # RN06: nao pode ser futura
    justificativa = Column(Text, nullable=False)
    referencia_comprovante = Column(String(150), nullable=False)  # RN05: unico por usuario
    situacao = Column(SAEnum(SituacaoSolicitacao), nullable=False, default=SituacaoSolicitacao.RASCUNHO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # quando foi criada
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # ultima alteracao

    # Relacoes
    solicitante = relationship("Usuario", back_populates="solicitacoes", foreign_keys=[solicitante_id])
    historico = relationship("HistoricoAnalise", back_populates="solicitacao", cascade="all, delete-orphan")

class HistoricoAnalise(Base):
    __tablename__ = "historico_analise"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)  # quem decidiu (RN12)
    etapa = Column(String(50), nullable=False)  # ex: gestor, financeiro, pagamento
    decisao = Column(String(50), nullable=False)  # ex: aprovada, recusada, enviada, paga
    observacao = Column(Text, nullable=True)  # obrigatoria se recusada (RN11)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # quando decidiu (RN12)

    # Relacoes
    solicitacao = relationship("Solicitacao", back_populates="historico")
    responsavel = relationship("Usuario")