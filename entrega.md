# NexusCorp - Entrega

API em Python + FastAPI + SQLite. Controle de reembolso com aprovação em 2 etapas, histórico de tudo e trava de permissão por perfil.

Como rodar: `pip install -r requirements.txt` / `python seed.py` / `uvicorn main:app --reload`
Docs: `http://127.0.0.1:8000/docs`
Front de teste: `http://127.0.0.1:8000/front`
Matriz viva: `http://127.0.0.1:8000/consultas/matriz`

Fluxo: rascunho → aguardando_gestor → aguardando_financeiro → aprovada → paga / recusada

---

# Bloco 1 pronto e testado. ✅

O que foi entregue:

4 tabelas criadas e validadas no SQLite: departamentos, usuarios, solicitacoes, historico_analise
Relacionamentos preservados: Departamento → Usuário → Solicitação → Histórico
senha_hash e nunca senha pura, já pensando na RN13

---

# Bloco 2 pronto e testado. ✅

O que foi entregue:

Login com JWT que expira em 1h (RN14)
Senha salva só como hash PBKDF2, nunca pura (RN13)
Erro de login genérico, não revela se o email ou a senha falhou (Cenário 03)
Cadastro e atualização sem campo de perfil/departamento, impossível se auto-promover (RN15 + Cenário 04)
Rota /auth/me pra provar que o token funciona

---

# Bloco 3 pronto e testado. ✅

O que foi entregue:

Criar reembolso sempre como rascunho, dono = quem está logado
Listar só as minhas, com filtro por situação e categoria
Ver detalhe só se for minha, se for de outro volta 404 igual como se não existisse (RN02 / Cenário 01)
Editar só em rascunho, depois que enviou trava (RN07 / Cenário 06)
Excluir só em rascunho
Enviar pro gestor: rascunho → aguardando_gestor
Histórico das minhas, com quem decidiu e quando (RN12)

---

# Bloco 4 pronto e testado. ✅

O que foi entregue:

Gestor lista só pendentes do seu departamento (Cenário 07)
Gestor aprova → vai pro financeiro. Gestor recusa → encerrada, com justificativa obrigatória
Financeiro aprova → fica APROVADA. Financeiro recusa → encerrada, com justificativa
Financeiro paga → só se estiver APROVADA
Ninguém aprova a própria solicitação, mesmo sendo gestor/financeiro
Todo passo registra no histórico quem, quando, o que decidiu

---

# Front visual pronto e testado. ✅

O que foi entregue:

Front simples em frontend/index.html, só pra testar com botão, sem regra nenhuma
Abre em http://127.0.0.1:8000/front
Login com 1 clique pra Ana, Bruno, Patrícia, Carlos e Fernanda
Criar reembolso, listar minhas, pendentes do gestor e pendentes do financeiro
Botões de Enviar, Editar, Excluir, Aprovar, Recusar e Marcar como paga
Log embaixo mostrando a resposta da API em JSON
Toda regra continua na API, o front só chama as mesmas rotas do Docs

---

# Bloco 5 Final pronto. Projeto fechado. ✅🎉

O que foi entregue:

Filtros completos em /consultas: por situação, categoria, data, valor e departamento
Resumo com contagem e valor total por situação, respeitando o escopo de quem chama
Matriz de permissões viva na API, não só no papel
README final pra entregar o projeto

---

# Como provar na homologação:

- Ana tenta ver reembolso do Bruno → 404, não vaza dado (RN02)
- Carlos tenta aprovar da Ana → 403, outro departamento (RN03)
- Login com senha errada → 401 genérico
- Ana tenta virar financeiro → ignorado, continua colaborador (RN15)
- Fernanda tenta aprovar antes do gestor → 400, fora de sequência (RN08)
- Ana envia R$ 180, tenta editar pra R$ 1800 → 400 travado (RN07)
- Patrícia lista pendentes → só Comercial (RN03)
- Fluxo completo → rascunho, envio, gestor, financeiro, paga, tudo no histórico (RN12)
