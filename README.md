# NexusCorp - Gestao de Reembolsos

API em Python + FastAPI + SQLite. Controle de reembolsos com aprovacao em 2 etapas, historico de decisoes e travas de seguranca.

## Como rodar

```bash
cd nexuscorp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000/
- Docs (Swagger): http://127.0.0.1:8000/docs
- Front visual de teste: http://127.0.0.1:8000/front
- Matriz de permissoes: http://127.0.0.1:8000/consultas/matriz

## Usuarios seed (senha de todos: 123456)

| Nome | Email | Perfil | Departamento |
| --- | --- | --- | --- |
| Ana | ana@nexuscorp.com | colaborador | Comercial (1) |
| Bruno | bruno@nexuscorp.com | colaborador | Tecnologia (2) |
| Patricia | patricia@nexuscorp.com | gestor | Comercial (1) |
| Carlos | carlos@nexuscorp.com | gestor | Tecnologia (2) |
| Fernanda | fernanda@nexuscorp.com | financeiro | Financeiro (3) |

## Fluxo

```
rascunho -> aguardando_gestor -> aguardando_financeiro -> aprovada -> paga
                                \-> recusada
                                                   \-> recusada
```

- Colaborador cria em rascunho, edita/exclui so em rascunho, envia para o gestor.
- Gestor aprova/recusa so do seu departamento, nunca a propria.
- Financeiro aprova/recusa so apos o gestor, paga so se APROVADA.
- Recusa sempre exige justificativa. Tudo fica no historico.

## Regras (RN)

- RN01 Sem token = 401 | RN02 Colaborador so ve as suas | RN03 Gestor so seu dept
- RN04 Valor > 0 | RN05 Sem comprovante duplicado | RN06 Sem data futura
- RN07 So rascunho pode ser modificado | RN08 Financeiro so apos gestor
- RN09 Ninguem aprova a propria | RN10 So paga se APROVADA
- RN11 Recusa exige justificativa | RN12 Historico de tudo
- RN13 Senha com hash PBKDF2, nunca legivel | RN14 Token expira em 1h
- RN15 Ninguem se auto-promove no cadastro/edicao

## Matriz de permissoes

| Acao | Colaborador | Gestor | Financeiro |
| --- | --- | --- | --- |
| Criar / Listar minhas | SIM | SIM (as suas) | SIM (as suas) |
| Editar / Excluir / Enviar | SIM, so rascunho, so as suas | SIM, so rascunho, so as suas | SIM, so rascunho, so as suas |
| Listar pendentes do gestor | NAO | SIM, so meu dept | NAO |
| Aprovar/Recusar como gestor | NAO | SIM, so meu dept, nunca a propria | NAO |
| Listar pendentes do financeiro | NAO | NAO | SIM, todas |
| Aprovar/Recusar como financeiro | NAO | NAO | SIM, so apos gestor, nunca a propria |
| Marcar como paga | NAO | NAO | SIM, so se APROVADA |
| Ver historico | SIM, so as suas | SIM, so meu dept | SIM, todas |

## Cenários de homologacao (8)

1. Ana tenta ver reembolso do Bruno -> 404, nao vaza dado (RN02)
2. Carlos (gestor Tecnologia) tenta aprovar da Ana (Comercial) -> 403 (RN03)
3. Login com senha errada -> 401 generico, sem dizer se email existe
4. Ana tenta se cadastrar/editar como financeiro -> ignorado, continua colaborador (RN15)
5. Fernanda tenta aprovar antes do gestor -> 400, fora de sequencia (RN08)
6. Ana envia R$ 180, tenta editar para R$ 1800 depois de enviado -> 400 travado (RN07)
7. Patricia lista pendentes -> so Comercial, nao ve Tecnologia (RN03)
8. Historico da solicitacao mostra: criacao, envio, aprovacao gestor, aprovacao financeiro, pagamento - com quem e quando (RN12)

## Estrutura

```
nexuscorp/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── security.py
├── seed.py
├── requirements.txt
├── README.md
├── routers/
│   ├── auth.py
│   ├── usuarios.py
│   ├── reembolsos.py
│   ├── aprovacoes.py
│   └── consultas.py
└── frontend/
    └── index.html
```


by: Gustavo Lima TDS 
gerado com suporte de IA