# routers/usuarios.py - Atualizacao de dados proprios, sem elevar permissao
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario
from schemas import UsuarioUpdate, UsuarioResponse
from security import get_usuario_atual, hash_senha

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# PATCH /usuarios/me - RN15: so nome e senha, NUNCA perfil ou departamento
@router.patch("/me", response_model=UsuarioResponse)
def atualizar_meus_dados(dados: UsuarioUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if dados.nome is not None:
        usuario.nome = dados.nome  # pode trocar o nome
    if dados.senha is not None:
        usuario.senha = None  # ignora campo inexistente, seguranca extra
        usuario.senha_hash = hash_senha(dados.senha)  # troca senha com hash
    # perfil e departamento_id NAO existem neste schema, entao nao tem como trocar
    db.commit()
    db.refresh(usuario)
    return usuario
