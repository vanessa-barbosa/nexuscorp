# routers/aprovacoes.py - Bloco 4: Gestor + Financeiro
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import Solicitacao, HistoricoAnalise, SituacaoSolicitacao, CategoriaDespesa, Usuario, PerfilUsuario
from schemas import SolicitacaoResponse, HistoricoResponse, DecisaoRequest
from security import get_usuario_atual

router = APIRouter(prefix="/aprovacoes", tags=["aprovacoes"])

# Helper: registra decisao no historico (RN12)
def _registrar(db: Session, sol: Solicitacao, usuario: Usuario, etapa: str, decisao: str, observacao: str = None):
    db.add(HistoricoAnalise(
        solicitacao_id=sol.id,
        responsavel_id=usuario.id,
        etapa=etapa,
        decisao=decisao,
        observacao=observacao,
    ))

# Helper: RN09 - ninguem aprova a propria solicitacao
def _bloquear_auto_aprovacao(sol: Solicitacao, usuario: Usuario):
    if sol.solicitante_id == usuario.id:
        raise HTTPException(status_code=403, detail="Voce nao pode aprovar uma solicitacao de sua propria autoria")

# Helper: busca solicitacao ou 404
def _buscar(db: Session, solicitacao_id: int) -> Solicitacao:
    sol = db.query(Solicitacao).filter(Solicitacao.id == solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    return sol

# Helper: exige perfil gestor ou financeiro
def _exigir(perfil: str, usuario: Usuario):
    if usuario.perfil.value != perfil:
        raise HTTPException(status_code=403, detail="Sem permissao para esta operacao")

# ============ GESTOR ============

# GET /aprovacoes/gestor - Listar pendentes DO MEU departamento (Cenario 07)
@router.get("/gestor", response_model=List[SolicitacaoResponse])
def listar_gestor(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _exigir("gestor", usuario)
    # Junta com Usuario para filtrar pelo departamento do SOLICITANTE
    q = db.query(Solicitacao).join(Usuario, Solicitacao.solicitante_id == Usuario.id).filter(
        Usuario.departamento_id == usuario.departamento_id  # RN03: so meu departamento
    )
    # Por padrao, mostra so quem aguarda o gestor. Se passar situacao, respeita o filtro.
    if situacao is not None:
        q = q.filter(Solicitacao.situacao == situacao)
    else:
        q = q.filter(Solicitacao.situacao == SituacaoSolicitacao.AGUARDANDO_GESTOR)
    if categoria is not None:
        q = q.filter(Solicitacao.categoria == categoria)
    return q.order_by(Solicitacao.id.asc()).all()

# POST /aprovacoes/gestor/{id}/aprovar - Gestor aprova -> vai para o financeiro
@router.post("/gestor/{solicitacao_id}/aprovar", response_model=SolicitacaoResponse)
def gestor_aprovar(solicitacao_id: int, dados: DecisaoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    _exigir("gestor", usuario)
    sol = _buscar(db, solicitacao_id)
    _bloquear_auto_aprovacao(sol, usuario)  # RN09
    # RN03: solicitante tem que ser do meu departamento
    solicitante = db.query(Usuario).filter(Usuario.id == sol.solicitante_id).first()
    if solicitante.departamento_id != usuario.departamento_id:
        raise HTTPException(status_code=403, detail="Solicitacao de outro departamento")
    # Fluxo: so pode aprovar quem esta aguardando gestor
    if sol.situacao != SituacaoSolicitacao.AGUARDANDO_GESTOR:
        raise HTTPException(status_code=400, detail="Solicitacao nao esta aguardando analise do gestor")
    sol.situacao = SituacaoSolicitacao.AGUARDANDO_FINANCEIRO  # RN08: so agora vai para o financeiro
    db.commit()
    _registrar(db, sol, usuario, etapa="gestor", decisao="aprovada", observacao=dados.observacao)
    db.commit()
    db.refresh(sol)
    return sol

# POST /aprovacoes/gestor/{id}/recusar - Gestor recusa -> encerrada, exige justificativa (RN11)
@router.post("/gestor/{solicitacao_id}/recusar", response_model=SolicitacaoResponse)
def gestor_recusar(solicitacao_id: int, dados: DecisaoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    _exigir("gestor", usuario)
    sol = _buscar(db, solicitacao_id)
    _bloquear_auto_aprovacao(sol, usuario)
    solicitante = db.query(Usuario).filter(Usuario.id == sol.solicitante_id).first()
    if solicitante.departamento_id != usuario.departamento_id:
        raise HTTPException(status_code=403, detail="Solicitacao de outro departamento")
    if sol.situacao != SituacaoSolicitacao.AGUARDANDO_GESTOR:
        raise HTTPException(status_code=400, detail="Solicitacao nao esta aguardando analise do gestor")
    # RN11: recusa sem justificativa = 400
    if not dados.observacao or not dados.observacao.strip():
        raise HTTPException(status_code=400, detail="Recusa exige justificativa no historico")
    sol.situacao = SituacaoSolicitacao.RECUSADA
    db.commit()
    _registrar(db, sol, usuario, etapa="gestor", decisao="recusada", observacao=dados.observacao)
    db.commit()
    db.refresh(sol)
    return sol

# ============ FINANCEIRO ============

# GET /aprovacoes/financeiro - Listar pendentes do financeiro
@router.get("/financeiro", response_model=List[SolicitacaoResponse])
def listar_financeiro(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _exigir("financeiro", usuario)
    q = db.query(Solicitacao)
    # Por padrao: aguardando financeiro + aprovadas (prontas para pagar)
    if situacao is not None:
        q = q.filter(Solicitacao.situacao == situacao)
    else:
        q = q.filter(Solicitacao.situacao.in_([SituacaoSolicitacao.AGUARDANDO_FINANCEIRO, SituacaoSolicitacao.APROVADA]))
    if categoria is not None:
        q = q.filter(Solicitacao.categoria == categoria)
    return q.order_by(Solicitacao.id.asc()).all()

# POST /aprovacoes/financeiro/{id}/aprovar - Financeiro aprova -> APROVADA (pronta para pagar)
@router.post("/financeiro/{solicitacao_id}/aprovar", response_model=SolicitacaoResponse)
def financeiro_aprovar(solicitacao_id: int, dados: DecisaoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    _exigir("financeiro", usuario)
    sol = _buscar(db, solicitacao_id)
    _bloquear_auto_aprovacao(sol, usuario)
    # RN08 / Cenario 05: financeiro NAO pode aprovar quem ainda aguarda o gestor
    if sol.situacao != SituacaoSolicitacao.AGUARDANDO_FINANCEIRO:
        raise HTTPException(status_code=400, detail="Solicitacao nao esta aguardando analise financeira")
    sol.situacao = SituacaoSolicitacao.APROVADA
    db.commit()
    _registrar(db, sol, usuario, etapa="financeiro", decisao="aprovada", observacao=dados.observacao)
    db.commit()
    db.refresh(sol)
    return sol

# POST /aprovacoes/financeiro/{id}/recusar - Financeiro recusa -> encerrada, exige justificativa
@router.post("/financeiro/{solicitacao_id}/recusar", response_model=SolicitacaoResponse)
def financeiro_recusar(solicitacao_id: int, dados: DecisaoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    _exigir("financeiro", usuario)
    sol = _buscar(db, solicitacao_id)
    _bloquear_auto_aprovacao(sol, usuario)
    if sol.situacao != SituacaoSolicitacao.AGUARDANDO_FINANCEIRO:
        raise HTTPException(status_code=400, detail="Solicitacao nao esta aguardando analise financeira")
    if not dados.observacao or not dados.observacao.strip():
        raise HTTPException(status_code=400, detail="Recusa exige justificativa no historico")
    sol.situacao = SituacaoSolicitacao.RECUSADA
    db.commit()
    _registrar(db, sol, usuario, etapa="financeiro", decisao="recusada", observacao=dados.observacao)
    db.commit()
    db.refresh(sol)
    return sol

# POST /aprovacoes/financeiro/{id}/pagar - RN10: so paga depois de APROVADA
@router.post("/financeiro/{solicitacao_id}/pagar", response_model=SolicitacaoResponse)
def financeiro_pagar(solicitacao_id: int, dados: DecisaoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    _exigir("financeiro", usuario)
    sol = _buscar(db, solicitacao_id)
    _bloquear_auto_aprovacao(sol, usuario)
    if sol.situacao != SituacaoSolicitacao.APROVADA:
        raise HTTPException(status_code=400, detail="Somente solicitacao aprovada pode ser marcada como paga")
    sol.situacao = SituacaoSolicitacao.PAGA
    db.commit()
    _registrar(db, sol, usuario, etapa="pagamento", decisao="paga", observacao=dados.observacao or "Pagamento registrado")
    db.commit()
    db.refresh(sol)
    return sol

# GET /aprovacoes/{id}/historico - Gestor ve do seu dept, financeiro ve tudo (Cenario 08)
@router.get("/{solicitacao_id}/historico", response_model=List[HistoricoResponse])
def historico_aprovacao(solicitacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sol = _buscar(db, solicitacao_id)
    if usuario.perfil.value == "gestor":
        solicitante = db.query(Usuario).filter(Usuario.id == sol.solicitante_id).first()
        if solicitante.departamento_id != usuario.departamento_id:
            raise HTTPException(status_code=403, detail="Solicitacao de outro departamento")
    elif usuario.perfil.value not in ("financeiro", "gestor"):
        # Colaborador usa a rota dele em /reembolsos, aqui e so gestor/financeiro
        if sol.solicitante_id != usuario.id:
            raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    return db.query(HistoricoAnalise).filter(HistoricoAnalise.solicitacao_id == sol.id).order_by(HistoricoAnalise.id.asc()).all()
