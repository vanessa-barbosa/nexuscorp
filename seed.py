# seed.py - Popula o banco com dados de teste (rodar uma vez)
# python seed.py
from database import SessionLocal, Base, engine
from models import Departamento, Usuario, PerfilUsuario
from security import hash_senha

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Limpa para nao duplicar se rodar 2x
db.query(Usuario).delete()
db.query(Departamento).delete()
db.commit()

# Departamentos
comercial = Departamento(nome="Comercial")
tecnologia = Departamento(nome="Tecnologia")
financeiro_dep = Departamento(nome="Financeiro")
db.add_all([comercial, tecnologia, financeiro_dep])
db.commit()
db.refresh(comercial); db.refresh(tecnologia); db.refresh(financeiro_dep)

# Usuarios de teste - senha de todos: 123456
usuarios = [
    Usuario(nome="Ana", email="ana@nexuscorp.com", senha_hash=hash_senha("123456"), perfil=PerfilUsuario.COLABORADOR, departamento_id=comercial.id),
    Usuario(nome="Bruno", email="bruno@nexuscorp.com", senha_hash=hash_senha("123456"), perfil=PerfilUsuario.COLABORADOR, departamento_id=tecnologia.id),
    Usuario(nome="Patricia", email="patricia@nexuscorp.com", senha_hash=hash_senha("123456"), perfil=PerfilUsuario.GESTOR, departamento_id=comercial.id),
    Usuario(nome="Carlos Gestor Tec", email="carlos@nexuscorp.com", senha_hash=hash_senha("123456"), perfil=PerfilUsuario.GESTOR, departamento_id=tecnologia.id),
    Usuario(nome="Fernanda Financeiro", email="fernanda@nexuscorp.com", senha_hash=hash_senha("123456"), perfil=PerfilUsuario.FINANCEIRO, departamento_id=financeiro_dep.id),
]
db.add_all(usuarios)
db.commit()
print("Seed OK - 3 departamentos, 5 usuarios, senha de todos: 123456")
db.close()
