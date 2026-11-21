# security.py - Hash de senha + JWT + usuario atual
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario

# Chave secreta do JWT - em producao viria de variavel de ambiente
SECRET_KEY = "nexuscorp-chave-secreta-trocar-em-producao-123"
ALGORITHM = "HS256"  # algoritmo de assinatura do token
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # RN14: token expira em 1h

# Hash com PBKDF2 da stdlib - sem passlib, sem bcrypt, sem limite de 72 bytes
# Formato salvo no banco: pbkdf2_sha256$600000$<salt_hex>$<hash_hex>
_ITERACOES = 600_000

# bearer_scheme = pede so o token no botao Authorize, sem username/password
bearer_scheme = HTTPBearer(auto_error=False)

# hash_senha: transforma senha pura em hash (RN13 - nunca salva legivel)
def hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)  # salt aleatorio de 16 bytes, em hex
    hash_bytes = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), _ITERACOES)
    return f"pbkdf2_sha256${_ITERACOES}${salt}${hash_bytes.hex()}"

# verificar_senha: compara senha digitada com o hash salvo
def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    try:
        # Separa o hash salvo nas 4 partes
        _, iteracoes_str, salt, hash_salvo = senha_hash.split("$")
        hash_novo = hashlib.pbkdf2_hmac("sha256", senha_pura.encode("utf-8"), salt.encode("utf-8"), int(iteracoes_str))
        # hmac.compare_digest = comparacao em tempo constante, anti timing-attack
        return hmac.compare_digest(hash_novo.hex(), hash_salvo)
    except (ValueError, AttributeError):
        return False  # hash em formato invalido = senha invalida

# criar_token: gera JWT com id do usuario e expiracao
def criar_token(dados: dict) -> str:
    dados_copia = dados.copy()  # copia para nao alterar o original
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_copia.update({"exp": expira})  # exp = quando o token deixa de valer
    return jwt.encode(dados_copia, SECRET_KEY, algorithm=ALGORITHM)

# get_usuario_atual: RN01 - toda rota protegida usa isso, sem token valido = 401
def get_usuario_atual(credenciais: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> Usuario:
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nao foi possivel validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Sem token no header = bloqueia direto
    if credenciais is None or not credenciais.credentials:
        raise erro_credenciais
    token = credenciais.credentials  # pega so o token, sem o "Bearer "
    try:
        # decodifica o token e pega o sub (subject = id do usuario)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: str = payload.get("sub")
        if usuario_id is None:
            raise erro_credenciais
    except JWTError:
        raise erro_credenciais  # token invalido ou expirado -> RN14 bloqueia
    # busca o usuario no banco pelo id do token
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise erro_credenciais
    return usuario

# exigir_perfil: fabrica de dependencia - so deixa passar se o perfil bater
def exigir_perfil(*perfis_permitidos: str):
    def checar(usuario: Usuario = Depends(get_usuario_atual)):
        if usuario.perfil.value not in perfis_permitidos:
            raise HTTPException(status_code=403, detail="Sem permissao para esta operacao")
        return usuario
    return checar
