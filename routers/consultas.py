# routers/consultas.py - Bloco 5 Final: filtros + matriz + resumo
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional, List, Dict, Any
from database import get_db
from models import Solicitacao, Usuario, SituacaoSolicitacao, CategoriaDespesa
from schemas import SolicitacaoResponse
from security import get_usuario_atual

router = APIRouter(prefix="/consultas", tags=["consultas"])

# Helper: aplica filtros comuns (situacao, categoria, data, valor)
def _filtros(q, situacao, categoria, data_inicio, data_fim, valor_min, valor_max):
    if situacao is not None:
        q = q.filter(Solicitacao.situacao == situacao)
    if categoria is not None:
        q = q.filter(Solicitacao.categoria == categoria)
    if data_inicio is not None:
        q = q.filter(Solicitacao.data_despesa >= data_inicio)
    if data_fim is not None:
        q = q.filter(Solicitacao.data_despesa <= data_fim)
    if valor_min is not None:
        q = q.filter(Solicitacao.valor >= valor_min)
    if valor_max is not None:
        q = q.filter(Solicitacao.valor <= valor_max)
    return q

# GET /consultas/minhas - Colaborador: minhas com todos os filtros
@router.get("/minhas", response_model=List[SolicitacaoResponse])
def minhas(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    valor_min: Optional[float] = Query(None, ge=0),
    valor_max: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    q = db.query(Solicitacao).filter(Solicitacao.solicitante_id == usuario.id)  # RN02
    q = _filtros(q, situacao, categoria, data_inicio, data_fim, valor_min, valor_max)
    return q.order_by(Solicitacao.id.desc()).all()

# GET /consultas/gestor - Gestor: so meu departamento, com filtros
@router.get("/gestor", response_model=List[SolicitacaoResponse])
def gestor(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    valor_min: Optional[float] = Query(None, ge=0),
    valor_max: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    # Gestor sem perfil gestor nao ve nada aqui - retorna vazio, nao vaza dado
    if usuario.perfil.value != "gestor":
        return []
    q = db.query(Solicitacao).join(Usuario, Solicitacao.solicitante_id == Usuario.id).filter(
        Usuario.departamento_id == usuario.departamento_id  # RN03
    )
    q = _filtros(q, situacao, categoria, data_inicio, data_fim, valor_min, valor_max)
    return q.order_by(Solicitacao.id.asc()).all()

# GET /consultas/financeiro - Financeiro: tudo, com filtro por departamento
@router.get("/financeiro", response_model=List[SolicitacaoResponse])
def financeiro(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    departamento_id: Optional[int] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    valor_min: Optional[float] = Query(None, ge=0),
    valor_max: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    if usuario.perfil.value != "financeiro":
        return []
    q = db.query(Solicitacao).join(Usuario, Solicitacao.solicitante_id == Usuario.id)
    if departamento_id is not None:
        q = q.filter(Usuario.departamento_id == departamento_id)
    q = _filtros(q, situacao, categoria, data_inicio, data_fim, valor_min, valor_max)
    return q.order_by(Solicitacao.id.asc()).all()

# GET /consultas/resumo - Contagem por situacao, respeitando o escopo de quem chama
@router.get("/resumo")
def resumo(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    # Base muda conforme o perfil: colaborador ve so as suas, gestor so seu dept, financeiro ve tudo
    q = db.query(Solicitacao.situacao, func.count(Solicitacao.id), func.coalesce(func.sum(Solicitacao.valor), 0))
    if usuario.perfil.value == "colaborador":
        q = q.filter(Solicitacao.solicitante_id == usuario.id)
    elif usuario.perfil.value == "gestor":
        q = q.join(Usuario, Solicitacao.solicitante_id == Usuario.id).filter(Usuario.departamento_id == usuario.departamento_id)
    # financeiro: sem filtro, ve tudo
    rows = q.group_by(Solicitacao.situacao).all()
    return {
        "usuario": usuario.nome,
        "perfil": usuario.perfil.value,
        "por_situacao": [
            {"situacao": situacao.value, "quantidade": qtd, "valor_total": float(total)}
            for situacao, qtd, total in rows
        ],
        "total_quantidade": sum(r[1] for r in rows),
        "total_valor": float(sum(r[2] for r in rows)),
    }

# GET /consultas/matriz - Matriz de permissoes (documentacao viva da API)
@router.get("/matriz")
def matriz():
    return {
        "matriz_permissoes": [
            {"acao": "Criar reembolso", "colaborador": "SIM (so as suas)", "gestor": "SIM (so as suas)", "financeiro": "SIM (so as suas)"},
            {"acao": "Listar minhas", "colaborador": "SIM", "gestor": "SIM (so as suas)", "financeiro": "SIM (so as suas)"},
            {"acao": "Editar / Excluir", "colaborador": "SIM, so em rascunho", "gestor": "SIM, so as suas em rascunho", "financeiro": "SIM, so as suas em rascunho"},
            {"acao": "Enviar para gestor", "colaborador": "SIM, so as suas", "gestor": "SIM, so as suas", "financeiro": "SIM, so as suas"},
            {"acao": "Listar pendentes do gestor", "colaborador": "NAO", "gestor": "SIM, so meu departamento", "financeiro": "NAO"},
            {"acao": "Aprovar / Recusar como gestor", "colaborador": "NAO", "gestor": "SIM, so meu dept, nunca a propria", "financeiro": "NAO"},
            {"acao": "Listar pendentes do financeiro", "colaborador": "NAO", "gestor": "NAO", "financeiro": "SIM, todas"},
            {"acao": "Aprovar / Recusar como financeiro", "colaborador": "NAO", "gestor": "NAO", "financeiro": "SIM, so apos gestor, nunca a propria"},
            {"acao": "Marcar como paga", "colaborador": "NAO", "gestor": "NAO", "financeiro": "SIM, so se APROVADA"},
            {"acao": "Ver historico", "colaborador": "SIM, so as suas", "gestor": "SIM, so meu dept", "financeiro": "SIM, todas"},
        ],
        "regras": {
            "RN01": "Sem token valido = 401",
            "RN02": "Colaborador so ve as suas",
            "RN03": "Gestor so ve seu departamento",
            "RN04": "Valor > 0",
            "RN05": "Sem comprovante duplicado por usuario",
            "RN06": "Sem data futura",
            "RN07": "So rascunho pode ser modificado",
            "RN08": "Financeiro so apos gestor",
            "RN09": "Ninguem aprova a propria",
            "RN10": "So paga se APROVADA",
            "RN11": "Recusa exige justificativa",
            "RN12": "Tudo registrado no historico",
            "RN13": "Senha nunca salva legivel (PBKDF2)",
            "RN14": "Token expira em 1h",
            "RN15": "Ninguem se auto-promove no cadastro/edicao",
        },
    }
