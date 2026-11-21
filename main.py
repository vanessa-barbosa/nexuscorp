# main.py - Ponto de entrada da API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routers import auth, usuarios, reembolsos, aprovacoes, consultas

# Cria todas as tabelas que ainda nao existem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NexusCorp - Gestao de Reembolsos", version="1.0.0")

# CORS: deixa o front em /front chamar a API sem bloqueio do navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(reembolsos.router)
app.include_router(aprovacoes.router)
app.include_router(consultas.router)

# Front de teste visual em /front - nao faz parte da homologacao, so para testar
app.mount("/front", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "NexusCorp - Bloco 5 Final: pronto", "front": "/front", "matriz": "/consultas/matriz"}
