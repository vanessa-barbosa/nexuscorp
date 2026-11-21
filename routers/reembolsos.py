# routers/reembolsos.py - Bloco 3: Colaborador (CRUD + enviar)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from database import get_db
from models import Solicitacao, HistoricoAnalise, SituacaoSolicitacao, CategoriaDespesa, Usuario
from schemas import SolicitacaoCreate, SolicitacaoUpdate, SolicitacaoResponse, HistoricoResponse
from security import get_usuario_atual

router = APIRouter(prefix="/reembolsos", tags=["reembolsos"])

# Helper: busca solicitacao OU da 404. Nunca revela se existe de outro usuario (RN02 / Cenario 01)
# Se nao for minha -> 404 igual como se nao existisse. Nao vaza dado do Bruno para a Ana.
def _minha_solicitacao(db: Session, solicitacao_id: int, usuario: Usuario) -> Solicitacao:
    sol = db.query(Solicitacao).filter(
        Solicitacao.id == solicitacao_id,
        Solicitacao.solicitante_id == usuario.id,  # RN02: so as minhas
    ).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    return sol

# Helper: registra um passo no historico (RN12 - quem, quando, o que)
def _registrar_historico(db: Session, sol: Solicitacao, usuario: Usuario, etapa: str, decisao: str, observacao: str = None):
    h = HistoricoAnalise(
        solicitacao_id=sol.id,
        responsavel_id=usuario.id,
        etapa=etapa,
        decisao=decisao,
        observacao=observacao,
    )
    db.add(h)

# Helper: RN05 - ja existe essa referencia para este usuario?
def _comprovante_duplicado(db: Session, usuario: Usuario, referencia: str, ignorar_id: int = None) -> bool:
    q = db.query(Solicitacao).filter(
        Solicitacao.solicitante_id == usuario.id,
        Solicitacao.referencia_comprovante == referencia,
    )
    if ignorar_id is not None:
        q = q.filter(Solicitacao.id != ignorar_id)  # na edicao, ignora ela mesma
    return q.first() is not None

# POST /reembolsos - Criar (sempre comeca em rascunho)
@router.post("", response_model=SolicitacaoResponse, status_code=201)
def criar(dados: SolicitacaoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    # RN06: data futura nao pode
    if dados.data_despesa > date.today():
        raise HTTPException(status_code=400, detail="Data da despesa nao pode ser futura")
    # RN05: mesmo comprovante, mesmo usuario = duplicado
    if _comprovante_duplicado(db, usuario, dados.referencia_comprovante):
        raise HTTPException(status_code=400, detail="Ja existe despesa com esta referencia de comprovante")
    # Cria: solicitante = quem esta logado, situacao = rascunho (nunca vem do cliente)
    sol = Solicitacao(
        solicitante_id=usuario.id,
        categoria=dados.categoria,
        valor=dados.valor,  # RN04 ja garantido pelo Field(gt=0) no schema
        data_despesa=dados.data_despesa,
        justificativa=dados.justificativa,
        referencia_comprovante=dados.referencia_comprovante,
        situacao=SituacaoSolicitacao.RASCUNHO,
    )
    db.add(sol)
    db.commit()
    db.refresh(sol)
    # Historico: registra a criacao
    _registrar_historico(db, sol, usuario, etapa="criacao", decisao="rascunho")
    db.commit()
    db.refresh(sol)
    return sol

# GET /reembolsos - Listar so as minhas, com filtros
@router.get("", response_model=List[SolicitacaoResponse])
def listar_minhas(
    situacao: Optional[SituacaoSolicitacao] = Query(None),
    categoria: Optional[CategoriaDespesa] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    q = db.query(Solicitacao).filter(Solicitacao.solicitante_id == usuario.id)  # RN02
    if situacao is not None:
        q = q.filter(Solicitacao.situacao == situacao)
    if categoria is not None:
        q = q.filter(Solicitacao.categoria == categoria)
    return q.order_by(Solicitacao.id.desc()).all()

# GET /reembolsos/{id} - Detalhe de uma minha
@router.get("/{solicitacao_id}", response_model=SolicitacaoResponse)
def detalhe(solicitacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return _minha_solicitacao(db, solicitacao_id, usuario)

# PATCH /reembolsos/{id} - Editar SO em rascunho (RN07 + Cenario 06)
@router.patch("/{solicitacao_id}", response_model=SolicitacaoResponse)
def editar(solicitacao_id: int, dados: SolicitacaoUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sol = _minha_solicitacao(db, solicitacao_id, usuario)
    # RN07: so rascunho pode ser modificado. Enviou -> travou. R$180 nao vira R$1800.
    if sol.situacao != SituacaoSolicitacao.RASCUNHO:
        raise HTTPException(status_code=400, detail="Somente solicitacoes em rascunho podem ser modificadas")
    # RN06: se trocou a data, valida de novo
    if dados.data_despesa is not None and dados.data_despesa > date.today():
        raise HTTPException(status_code=400, detail="Data da despesa nao pode ser futura")
    # RN05: se trocou o comprovante, valida duplicidade de novo
    if dados.referencia_comprovante is not None and _comprovante_duplicado(db, usuario, dados.referencia_comprovante, ignorar_id=sol.id):
        raise HTTPException(status_code=400, detail="Ja existe despesa com esta referencia de comprovante")
    # Aplica so os campos que vieram (exclude_unset = so o que o cliente mandou)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(sol, campo, valor)
    db.commit()
    db.refresh(sol)
    return sol

# DELETE /reembolsos/{id} - Excluir SO em rascunho
@router.delete("/{solicitacao_id}", status_code=204)
def excluir(solicitacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sol = _minha_solicitacao(db, solicitacao_id, usuario)
    # So rascunho pode ser excluido. Enviada, aprovada, paga, recusada = nao.
    if sol.situacao != SituacaoSolicitacao.RASCUNHO:
        raise HTTPException(status_code=400, detail="Somente solicitacoes em rascunho podem ser excluidas")
    db.delete(sol)
    db.commit()
    return None

# POST /reembolsos/{id}/enviar - Rascunho -> Aguardando gestor
@router.post("/{solicitacao_id}/enviar", response_model=SolicitacaoResponse)
def enviar(solicitacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sol = _minha_solicitacao(db, solicitacao_id, usuario)
    if sol.situacao != SituacaoSolicitacao.RASCUNHO:
        raise HTTPException(status_code=400, detail="Somente rascunho pode ser enviado para aprovacao")
    sol.situacao = SituacaoSolicitacao.AGUARDANDO_GESTOR
    db.commit()
    _registrar_historico(db, sol, usuario, etapa="envio", decisao="aguardando_gestor", observacao="Enviada para analise do gestor")
    db.commit()
    db.refresh(sol)
    return sol

# GET /reembolsos/{id}/historico - Acompanhar historico das minhas
@router.get("/{solicitacao_id}/historico", response_model=List[HistoricoResponse])
def historico(solicitacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sol = _minha_solicitacao(db, solicitacao_id, usuario)  # RN02 tambem no historico
    return db.query(HistoricoAnalise).filter(HistoricoAnalise.solicitacao_id == sol.id).order_by(HistoricoAnalise.id.asc()).all()
