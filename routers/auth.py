# routers/auth.py - Login e registro
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, PerfilUsuario
from schemas import LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse
from security import hash_senha, verificar_senha, criar_token, get_usuario_atual

router = APIRouter(prefix="/auth", tags=["auth"])

# POST /auth/registrar - cria usuario como colaborador padrao (RN15)
@router.post("/registrar", response_model=UsuarioResponse, status_code=201)
def registrar(dados: UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o email ja existe
    existe = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")
    # 2. Cria usuario SEMPRE como colaborador, departamento 1 temporario
    # Em producao o departamento viria de convite/admin. Aqui fixamos
    # para o Bloco 2 funcionar - Bloco 5/seed vai organizar isso.
    novo = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),  # RN13: salva hash, nao senha pura
        perfil=PerfilUsuario.COLABORADOR,  # RN15: ignora qualquer perfil enviado
        departamento_id=1,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

# POST /auth/login - RN01 + Cenario 03 (senha errada = 401 generico)
@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    # 1. Busca usuario pelo email
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    # 2. Se nao achou OU senha errada -> mesmo erro generico (nao revela o que falhou)
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")
    # 3. Gera token com o id do usuario no campo sub
    token = criar_token({"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}

# GET /auth/me - retorna quem esta logado (prova que o token funciona)
@router.get("/me", response_model=UsuarioResponse)
def me(usuario: Usuario = Depends(get_usuario_atual)):
    return usuario
