# NexusCorp - Documentação

API em Python + FastAPI + SQLite. Controle de reembolso com aprovação em 2 etapas, histórico de tudo e trava de permissão por perfil.

Como rodar: `pip install -r requirements.txt` / `python seed.py` / `uvicorn main:app --reload`
Docs: `http://127.0.0.1:8000/docs`
Front de teste: `http://127.0.0.1:8000/front`
Matriz viva: `http://127.0.0.1:8000/consultas/matriz`

Fluxo: rascunho → aguardando_gestor → aguardando_financeiro → aprovada → paga / recusada

---

# Bloco 1:

O que cada arquivo faz, linha por linha

- database.py

SQLALCHEMY_DATABASE_URL = aponta pro arquivo nexuscorp.db
create_engine = abre a conexão com o SQLite
SessionLocal = fábrica de sessões, uma por requisição
Base = classe mãe de todas as tabelas
get_db() = abre, entrega e fecha a sessão. É isso que o FastAPI vai usar em toda rota.

- models.py

PerfilUsuario = colaborador / gestor / financeiro
CategoriaDespesa = alimentacao / transporte / hospedagem / materiais
SituacaoSolicitacao = rascunho → aguardando_gestor → aguardando_financeiro → aprovada → paga / recusada
Departamento = id + nome único
Usuario = nome, email único (é o login), senha_hash, perfil, departamento_id (FK)
Solicitacao = solicitante_id (FK), categoria, valor, data_despesa, justificativa, referencia_comprovante, situacao
HistoricoAnalise = solicitacao_id (FK), responsavel_id (FK), etapa, decisao, observacao, created_at. É aqui que mora a RN12, rastreabilidade.

- main.py

Base.metadata.create_all = cria as tabelas se não existirem
FastAPI(...) = cria a app
@app.get("/") = rota de saúde, só pra confirmar que subiu

---

# Bloco 2:

O que cada arquivo faz, linha por linha

- security.py

SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES = 60 = config do JWT
PBKDF2 (hashlib, 600 mil iterações) = motor do hash. Sem passlib, sem bcrypt.
bearer_scheme = lê o header Authorization: Bearer <token>
hash_senha() = senha pura → hash com salt aleatório. Formato: pbkdf2_sha256$600000$salt$hash
verificar_senha() = refaz o hash com o mesmo salt e compara em tempo constante
criar_token() = gera JWT com sub = id do usuário + exp
get_usuario_atual() = RN01. Decodifica o token, busca o usuário. Token inválido/expirado → 401
exigir_perfil() = fábrica. Ex: exigir_perfil("gestor") só deixa gestor passar, resto leva 403

- schemas.py

LoginRequest = email + senha
TokenResponse = token
UsuarioCreate = só nome, email, senha. Sem perfil, sem departamento. É a trava da RN15.
UsuarioResponse = id, nome, email, perfil, departamento. Sem senha_hash. É a trava da RN13.
UsuarioUpdate = só nome e senha. Sem perfil, sem departamento.
SolicitacaoCreate = categoria, valor > 0, data, justificativa, referencia. Sem solicitante_id, sem situacao. O backend define.
SolicitacaoUpdate = mesmos campos, todos opcionais. Sem solicitante_id, sem situacao.
SolicitacaoResponse = tudo + historico junto
DecisaoRequest = só observacao. Obrigatória na recusa, opcional na aprovação.

- routers/auth.py

POST /auth/registrar = cria sempre como COLABORADOR. Mesmo que mandem perfil no JSON, ele é ignorado.
POST /auth/login = busca por email, verifica senha, erro genérico 401 se qualquer um falhar.
GET /auth/me = retorna o usuário do token.

- routers/usuarios.py

PATCH /usuarios/me = só troca nome e senha. Não tem como trocar perfil/departamento por essa rota.

- seed.py

Limpa e cria 3 departamentos + 5 usuários dos cenários de homologação. Roda com python seed.py.
Ana (colaborador, Comercial), Bruno (colaborador, Tecnologia), Patricia (gestor, Comercial), Carlos (gestor, Tecnologia), Fernanda (financeiro, Financeiro). Senha de todos: 123456.

---

# Bloco 3:

O que cada parte faz, linha por linha

- _minha_solicitacao()

Filtra por id E solicitante_id == usuario.id. Se não for minha, 404. É isso que impede a Ana de ver a do Bruno sem vazar que ela existe.

- criar()

Valida RN06 data futura, RN05 duplicado, cria com solicitante_id = usuario.id e situacao = rascunho. O cliente não manda dono nem situação.
Registra no histórico criacao / rascunho.

- listar_minhas() / detalhe()

Listar só as minhas, com filtro por situação e categoria.
Detalhe só se for minha, senão 404.

- editar()

Trava RN07: se não for rascunho, 400. Revalida RN06 e RN05 se trocar data/comprovante.
model_dump(exclude_unset=True) = só aplica os campos que vieram no PATCH.

- excluir() / enviar()

Excluir só em rascunho, senão 400.
Enviar só de rascunho → aguardando_gestor + histórico envio.

- historico()

Lista o histórico das minhas, em ordem. RN12 também aqui.

# BLOCO 4:

O que cada parte faz, linha por linha

- listar_gestor()

join com Usuario + filtro departamento_id == usuario.departamento_id. É isso que faz o Cenário 07 funcionar: Patrícia nunca vê Tecnologia.

- gestor_aprovar() / gestor_recusar()

Trava perfil gestor, trava RN09 auto-aprovação, trava RN03 departamento, trava fluxo só se aguardando_gestor.
Aprovar → aguardando_financeiro. Recusar → exige observacao (RN11) → recusada.

- listar_financeiro()

Financeiro vê tudo. Por padrão mostra aguardando_financeiro + aprovada (pronta pra pagar).

- financeiro_aprovar() / financeiro_recusar() / financeiro_pagar()

Aprovar só se aguardando_financeiro, senão é o Cenário 05.
Pagar só se aprovada, senão é a RN10.
Recusar exige justificativa, RN11.

- _registrar()

Cada decisão vira uma linha no HistoricoAnalise com responsavel_id + created_at automático. É a RN12.

- historico_aprovacao()

Gestor vê só seu dept, financeiro vê tudo, colaborador só as suas.

Bloco 4 fechado. O fluxo completo está de pé: rascunho → gestor → financeiro → aprovada → paga.

---

# Front visual:

O que cada parte faz, linha por linha

- frontend/index.html

Só pra testar, sem regra. Toda regra continua na API.
Login com 1 clique pra Ana, Bruno, Patrícia, Carlos e Fernanda.
Criar, listar minhas, pendentes do gestor, pendentes do financeiro.
Botões Enviar, Editar, Excluir, Aprovar, Recusar, Pagar.
Log embaixo mostrando a resposta da API em JSON.
Abre em /front. No Linux tem que ser index.html minúsculo, Index.html dá 404.

- main.py

CORS liberado pro front chamar a API sem bloqueio do navegador.
app.mount("/front", ...) = serve o frontend/index.html.

---

# BLOCO 5:

O que cada parte faz, linha por linha

- _filtros()

Aplica só os filtros que vieram: situacao, categoria, data_inicio, data_fim, valor_min, valor_max. É o mesmo helper pras 3 listas, pra não repetir código.

- consultas/minhas()

Filtra por solicitante_id == usuario.id. É a RN02 de novo, só que com todos os filtros.

- consultas/gestor()

Se não for gestor, retorna lista vazia, não vaza dado.
Join com Usuario + filtro departamento_id == usuario.departamento_id. É a RN03 de novo, só que com filtros.

- consultas/financeiro()

Se não for financeiro, retorna lista vazia.
Join com Usuario, sem travar departamento. Se passar departamento_id, filtra por ele.
É o único que vê tudo.

- resumo()

Conta quantas e soma quanto por situacao.
Colaborador conta só as suas, gestor só do seu departamento, financeiro conta tudo.
Devolve por_situacao, total_quantidade e total_valor.

- matriz()

Devolve a matriz de permissões + as 15 RNs em JSON. É a documentação viva, abre em /consultas/matriz.

- main.py

Só adicionou from routers import consultas e app.include_router(consultas.router). Sem isso as rotas novas existem mas não funcionam.

- README.md

Como rodar, usuários seed, fluxo, RNs, matriz e os 8 cenários. É o que vai junto na entrega.

Bloco 5 fechado. Projeto pronto: rascunho → gestor → financeiro → aprovada → paga, com filtros, resumo, matriz e README.

---

# Contrato das operações (item 9.3):

O que cada rota faz, linha por linha

- POST /auth/registrar = cria como colaborador. 201. 400 se email duplicado.
- POST /auth/login = devolve JWT 1h. 200. 401 genérico se errar.
- GET /auth/me = quem sou eu. 200. 401 sem token.
- PATCH /usuarios/me = troca nome/senha. 200. 401 sem token.
- POST /reembolsos = cria em rascunho. 201. 400 data futura/duplicado. 422 valor <= 0.
- GET /reembolsos = só as minhas. 200. 401 sem token.
- GET /reembolsos/{id} = detalhe. 200. 404 se não for minha.
- PATCH /reembolsos/{id} = edita só rascunho. 200. 400 se já enviou.
- DELETE /reembolsos/{id} = exclui só rascunho. 204. 400 se já enviou.
- POST /reembolsos/{id}/enviar = rascunho → aguardando_gestor. 200. 400 se não for rascunho.
- GET /reembolsos/{id}/historico = histórico das minhas. 200. 404 se não for minha.
- GET /aprovacoes/gestor = pendentes do meu dept. 200. 403 se não for gestor.
- POST /aprovacoes/gestor/{id}/aprovar = → aguardando_financeiro. 200. 403 outro dept / própria. 400 fluxo errado.
- POST /aprovacoes/gestor/{id}/recusar = → recusada. 200. 400 sem justificativa.
- GET /aprovacoes/financeiro = pendentes + aprovadas. 200. 403 se não for financeiro.
- POST /aprovacoes/financeiro/{id}/aprovar = → aprovada. 200. 400 se ainda com gestor.
- POST /aprovacoes/financeiro/{id}/recusar = → recusada. 200. 400 sem justificativa.
- POST /aprovacoes/financeiro/{id}/pagar = → paga. 200. 400 se não estiver APROVADA.
- GET /aprovacoes/{id}/historico = histórico com escopo. 200. 403 / 404.
- GET /consultas/minhas = minhas com filtros. 200. 401 sem token.
- GET /consultas/gestor = meu dept com filtros. 200. Lista vazia se não for gestor.
- GET /consultas/financeiro = tudo com filtros. 200. Lista vazia se não for financeiro.
- GET /consultas/resumo = contagem + soma por situação. 200. 401 sem token.
- GET /consultas/matriz = matriz + RNs. 200.

---

# Matriz de permissões (item 9.4):

- Criar reembolso = colaborador SIM (só as suas) / gestor SIM (só as suas) / financeiro SIM (só as suas)
- Listar minhas = SIM / SIM / SIM
- Editar / Excluir = só rascunho, só as suas / só rascunho, só as suas / só rascunho, só as suas
- Enviar = só as suas / só as suas / só as suas
- Listar pendentes do gestor = NÃO / SIM, só meu dept / NÃO
- Aprovar / Recusar como gestor = NÃO / SIM, só meu dept, nunca a própria / NÃO
- Listar pendentes do financeiro = NÃO / NÃO / SIM, todas
- Aprovar / Recusar como financeiro = NÃO / NÃO / SIM, só após gestor, nunca a própria
- Marcar como paga = NÃO / NÃO / SIM, só se APROVADA
- Ver histórico = só as suas / só meu dept / todas

---

# Regras de negócio (item 9.5):

- RN01 = sem token válido, 401
- RN02 = colaborador só vê as suas
- RN03 = gestor só vê seu departamento
- RN04 = valor > 0
- RN05 = sem comprovante duplicado por usuário
- RN06 = sem data futura
- RN07 = só rascunho pode ser modificado
- RN08 = financeiro só após gestor
- RN09 = ninguém aprova a própria
- RN10 = só paga se APROVADA
- RN11 = recusa exige justificativa
- RN12 = tudo registrado no histórico
- RN13 = senha nunca salva legível, só hash PBKDF2
- RN14 = token expira em 1h
- RN15 = ninguém se auto-promove no cadastro / edição

---

# Decisões de segurança (item 9.6):

- JWT com exp de 1h, sem token = 401
- Senha só como hash PBKDF2 com salt, nunca pura, nunca devolvida na resposta
- Login com erro genérico, não revela se o email existe ou se a senha errou
- Schema sem perfil / departamento / solicitante_id / situacao, não dá pra falsificar dono, cargo ou status pelo JSON
- Checagem antes do commit, operação não autorizada não altera o banco
- 401 = sem identificação, 403 = sem permissão, 404 = não é minha / não existe, 400 = regra de negócio, 422 = formato inválido
- SECRET_KEY e CORS aberto são de teste, em produção viriam de variável de ambiente e origem restrita

---

# Erros que já peguei:

- passlib / bcrypt quebrou → trocou por PBKDF2 da stdlib
- del no Linux → usar rm
- email-validator faltando → pip install email-validator
- Bearer Bearer → no Docs colar só o token, no curl Bearer uma vez
- Index.html 404 → no Linux tem que ser index.html minúsculo
- 401 = sem token ou expirado, logar de novo
- 403 = logado mas sem permissão, trocar de usuário
- 400 = regra travou, ler o detail
- 422 = Pydantic barrou o formato
