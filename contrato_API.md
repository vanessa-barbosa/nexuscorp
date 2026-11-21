## Contrato das operações (item 9.3)

| Rota | Método | Quem pode | O que faz | Sucesso | Erro |
| --- | --- | --- | --- | --- | --- |
| /auth/registrar | POST | Qualquer um | Cria usuário sempre como colaborador | 201 | 400 email duplicado, 422 formato |
| /auth/login | POST | Qualquer um | Devolve JWT 1h | 200 | 401 genérico |
| /auth/me | GET | Logado | Quem sou eu | 200 | 401 sem token |
| /usuarios/me | PATCH | Logado | Troca nome/senha, nunca perfil | 200 | 401 |
| /reembolsos | POST | Logado | Cria em rascunho | 201 | 400 data futura/duplicado, 422 valor <=0 |
| /reembolsos | GET | Logado | Lista só as minhas | 200 | 401 |
| /reembolsos/{id} | GET | Dono | Detalhe | 200 | 404 se não for minha |
| /reembolsos/{id} | PATCH | Dono | Edita só em rascunho | 200 | 400 se já enviou |
| /reembolsos/{id} | DELETE | Dono | Exclui só em rascunho | 204 | 400 se já enviou |
| /reembolsos/{id}/enviar | POST | Dono | rascunho -> aguardando_gestor | 200 | 400 se não for rascunho |
| /reembolsos/{id}/historico | GET | Dono | Histórico | 200 | 404 |
| /aprovacoes/gestor | GET | Gestor | Pendentes do meu dept | 200 | 403 se não for gestor |
| /aprovacoes/gestor/{id}/aprovar | POST | Gestor | -> aguardando_financeiro | 200 | 403 outro dept / própria, 400 fluxo |
| /aprovacoes/gestor/{id}/recusar | POST | Gestor | -> recusada, exige justificativa | 200 | 400 sem justificativa |
| /aprovacoes/financeiro | GET | Financeiro | Pendentes + aprovadas | 200 | 403 |
| /aprovacoes/financeiro/{id}/aprovar | POST | Financeiro | -> aprovada | 200 | 400 se ainda com gestor |
| /aprovacoes/financeiro/{id}/recusar | POST | Financeiro | -> recusada, exige justificativa | 200 | 400 sem justificativa |
| /aprovacoes/financeiro/{id}/pagar | POST | Financeiro | -> paga | 200 | 400 se não estiver APROVADA |
| /aprovacoes/{id}/historico | GET | Gestor/Financeiro | Histórico com escopo | 200 | 403 / 404 |
| /consultas/minhas | GET | Logado | Minhas com filtros | 200 | 401 |
| /consultas/gestor | GET | Gestor | Meu dept com filtros | 200 | [] se não for gestor |
| /consultas/financeiro | GET | Financeiro | Tudo com filtros | 200 | [] se não for financeiro |
| /consultas/resumo | GET | Logado | Contagem + soma por situação | 200 | 401 |
| /consultas/matriz | GET | Qualquer um | Matriz + RNs | 200 | - |