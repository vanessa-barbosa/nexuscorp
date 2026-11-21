# NexusCorp - Evidências

Como gerar: `python seed.py` / `uvicorn main:app --reload` / testar em /docs ou /front
Em cada passo, cola o que a API devolveu. Não precisa print, o JSON já é a prova.

---

# Fluxo completo:

O que foi testado:

- Ana cria → 201, situacao = rascunho
- Ana envia → 200, situacao = aguardando_gestor
- Patrícia aprova → 200, situacao = aguardando_financeiro
- Fernanda aprova → 200, situacao = aprovada
- Fernanda paga → 200, situacao = paga
- Histórico → criacao, envio, gestor, financeiro, pagamento

Cole aqui o JSON do histórico:

```
COLE AQUI O JSON DE GET /aprovacoes/{id}/historico
Tem que mostrar: criacao, envio, gestor, financeiro, pagamento, com responsavel_id e created_at
```

---

# Acessos não autorizados:

O que foi testado:

- Sem token → 401
- Ana tenta ver reembolso do Bruno → 404, não vaza dado (RN02 / Cenário 01)
- Carlos tenta aprovar da Ana → 403, outro departamento (RN03 / Cenário 02)
- Login com senha errada → 401 genérico, não revela se o email existe (Cenário 03)
- Ana tenta virar financeiro → ignorado, continua colaborador (RN15 / Cenário 04)
- Fernanda tenta aprovar antes do gestor → 400, fora de sequência (RN08 / Cenário 05)
- Ana envia R$ 180, tenta editar pra R$ 1800 → 400 travado (RN07 / Cenário 06)
- Patrícia lista pendentes → só Comercial, não vê Tecnologia (RN03 / Cenário 07)
- Pagar sem estar APROVADA → 400 (RN10)

Cole aqui os JSON de cada bloqueio:

```
1. Sem token:
COLE AQUI O 401

2. Ana tenta ver do Bruno:
COLE AQUI O 404

3. Carlos tenta aprovar Comercial:
COLE AQUI O 403

4. Senha errada:
COLE AQUI O 401 genérico

5. Ana tenta virar financeiro:
COLE AQUI O /auth/me mostrando perfil = colaborador

6. Fernanda aprova antes do gestor:
COLE AQUI O 400

7. Editar enviado R$ 180 -> R$ 1800:
COLE AQUI O 400 "Somente solicitacoes em rascunho podem ser modificadas"

8. Patrícia lista pendentes:
COLE AQUI A LISTA SÓ COM COMERCIAL

9. Pagar sem estar APROVADA:
COLE AQUI O 400 "Somente solicitacao aprovada pode ser marcada como paga"
```

---

# Resumo e matriz:

O que foi testado:

- GET /consultas/resumo → contagem e soma por situação
- GET /consultas/matriz → matriz + RN01 até RN15

Cole aqui:

```
Resumo:
COLE AQUI O JSON DE /consultas/resumo

Matriz:
COLE AQUI O JSON DE /consultas/matriz OU PRINT DA TELA
```

---

# Como eu testei:

- Seed: `python seed.py` → 3 departamentos, 5 usuários, senha 123456
- API: `uvicorn main:app --reload` → http://127.0.0.1:8000/
- Docs: http://127.0.0.1:8000/docs
- Front: http://127.0.0.1:8000/front


# Testes:

CoreBox:~/Documentos/Projeto NextCorp/nexuscorp$ python3 -c "import sqlite3, json; con=sqlite3.connect('nexuscorp.db'); print(con.execute('SELECT * FROM historico_analise').fetchall()); print(con.execute('SELECT * FROM solicitacoes').fetchall())"
[(1, 1, 1, 'criacao', 'rascunho', None, '2026-11-21 14:13:11'), (2, 1, 1, 'envio', 'aguardando_gestor', 'Enviada para analise do gestor', '2026-11-21 14:13:50'), (3, 1, 3, 'gestor', 'aprovada', '', '2026-11-21 14:15:35'), (4, 1, 5, 'financeiro', 'aprovada', '', '2026-11-21 14:16:36'), (5, 1, 5, 'pagamento', 'paga', 'Pagamento registrado', '2026-11-21 14:17:01')]
[(1, 1, 'ALIMENTACAO', 180.0, '2026-11-21', 'Almoço com cliente', 'NF-TESTE-1', 'PAGA', '2026-11-21 14:13:11', '2026-11-21 14:17:01')]