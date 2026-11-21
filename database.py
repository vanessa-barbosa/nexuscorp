# database.py - Conexao com o banco SQLite + sessao
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL do banco: arquivo local nexuscorp.db na mesma pasta do projeto
SQLALCHEMY_DATABASE_URL = "sqlite:///./nexuscorp.db"

# create_engine = cria a conexao com o banco
# connect_args check_same_thread=False = permite o FastAPI usar SQLite em varias threads
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal = fabrica de sessoes (cada requisicao usa uma sessao)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = classe mae de todos os modelos (tabelas)
Base = declarative_base()

# get_db = dependencia do FastAPI: abre sessao, entrega, fecha no fim
def get_db():
    db = SessionLocal()  # abre uma sessao nova
    try:
        yield db  # entrega a sessao para a rota usar
    finally:
        db.close()  # fecha a sessao, mesmo se der erro