# API — como consumir as rotas

Todas as rotas expostas hoje, na ordem em que se usa. Base local: `http://localhost:8000`.
Swagger interativo em `http://localhost:8000/docs`.

Subir a API:

```bash
uvicorn src.main:app --reload
```

---

## Resumo

| # | Método | Rota | Para quê |
|---|---|---|---|
| 1 | `POST` | `/prefix/create` | cadastra um prefixo (UF) |
| 2 | `PUT` | `/prefix/update` | liga/desliga um prefixo |
| 3 | `GET` | `/prefix/all` | lista todos os prefixos |
| 4 | `GET` | `/preview` | espia os blocos sem gravar nada |
| 5 | `POST` | `/start` | **preparação** — tira a foto e salva no banco |
| 6 | `GET` | `/dispatch/{id}` | consulta a foto (blocos + avisos) |
| 7 | `PATCH` | `/dispatch/{id}/block/{block_id}` | tira bloco / troca email antes de enviar |
| 8 | `POST` | `/dispatch/{id}/e  xecute` | **envia** (202, roda em background) ⚠️ ver nota |
| 9 | `GET` | `/dispatch/{id}/status` | acompanha o progresso |

O fluxo real é sempre: **`/preview` → `/start` → conferir → `PATCH` → `execute` → `status`**.

---

## Antes de qualquer coisa: as travas do `.env`

Duas variáveis mudam o comportamento do `execute` e aparecem em **toda** resposta de dispatch:

```env
MAIL_SENDING_DISABLED=True
MAIL_REDIRECT_ALL_TO=seu.email@dominio.com
```

| campo na resposta | vem de | efeito |
|---|---|---|
| `mail_sending_disabled` | `MAIL_SENDING_DISABLED` | `true` = monta a mensagem e não conecta no SMTP |
| `mail_redirected_to` | `MAIL_REDIRECT_ALL_TO` | se preenchido, **todo** email vai pra esse endereço |

⚠️ **Com `mail_sending_disabled=true`, o `execute` marca os blocos como `SENT` mesmo sem
enviar nada.** O `SUPPRESS_SEND` do `fastapi-mail` não levanta exceção, então o
[dispatch_sender.py:44](../src/service/dispatch/dispatch_sender.py#L44) considera sucesso.
E o `find_blocks_to_send` filtra `status != SENT`, ou seja: aquele dispatch fica queimado e
nunca mais reenvia. Se for testar de verdade, ajuste o `.env`, **reinicie o uvicorn** e só
então faça um `/start` novo — o `ConnectionConfig` é montado no import do módulo.

---

## 1. `POST /prefix/create`

Cadastra um prefixo. O nome é normalizado pra maiúsculo (`sp` → `SP`) e nasce sempre com
`required_prefix: true`.

**Request**

```json
{ "prefix_name": "SP" }
```

| campo | tipo | regra |
|---|---|---|
| `prefix_name` | string | obrigatório, 2 a 3 caracteres |

**Response `200`**

```json
{
  "prefix_name": "SP",
  "required_prefix": true,
  "create_at": "2026-08-18T14:40:00"
}
```

**Erros** — `409` prefixo já existe · `422` nome vazio ou fora de 2–3 caracteres

```bash
curl -X POST http://localhost:8000/prefix/create \
  -H "Content-Type: application/json" \
  -d '{"prefix_name":"SP"}'
```

---

## 2. `PUT /prefix/update`

Liga ou desliga um prefixo. Só o `required_prefix` é alterável — o `prefix_name` aqui serve
de **chave de busca**, não é renomeação.

Desligar (`false`) tira o prefixo do `mount_block_files()`: ele some do `/preview` e dos
próximos `/start`. É assim que se aposenta uma UF sem apagar histórico.

**Request**

```json
{ "prefix_name": "SP", "prefix_required": false }
```

⚠️ Repare na inversão: o **request** manda `prefix_required`, a **response** devolve
`required_prefix`. Não é erro de digitação da doc, é assim no código
([prefix_update_request.py](../src/schema/request/prefix/prefix_update_request.py) vs
[prefix_response.py](../src/schema/response/prefix/prefix_response.py)).

**Response `200`** — mesmo formato do `create`.

**Erros** — `404` prefixo não existe · `422` nome vazio

```bash
curl -X PUT http://localhost:8000/prefix/update \
  -H "Content-Type: application/json" \
  -d '{"prefix_name":"SP","prefix_required":false}'
```

---

## 3. `GET /prefix/all`

Lista **todos** os prefixos, ativos e inativos. Sem paginação, sem filtro.

**Response `200`**

```json
[
  { "prefix_name": "AC", "required_prefix": true,  "create_at": "2026-08-13T10:00:00" },
  { "prefix_name": "AL", "required_prefix": true,  "create_at": "2026-08-13T10:00:00" },
  { "prefix_name": "SP", "required_prefix": false, "create_at": "2026-08-13T10:00:00" }
]
```

```bash
curl http://localhost:8000/prefix/all
```

---

## 4. `GET /preview`

Lê a pasta do `FILES_DIR_PATH`, agrupa os arquivos por prefixo ativo e devolve os blocos.
**Não grava nada no banco.** É a rota segura pra conferir se os arquivos estão nomeados certo
antes de criar um dispatch.

Só entram arquivos com sufixo `.pdf`, `.xls`, `.xlsx` ou `.txt` — a busca é recursiva
(`rglob`), então subpasta também conta. Um arquivo pertence ao prefixo se o nome começa com
ele **e** o caractere seguinte não é letra. Por isso `SP.pdf` e `SP_2026.pdf` entram em `SP`,
mas `SPAM.pdf` não.

**Response `200`**

```json
[
  {
    "prefix": "AC",
    "files": [
      "C:\\...\\AC.pdf",
      "C:\\...\\AC.TXT",
      "C:\\...\\AC.XLSX"
    ],
    "email": "ac@sebraeprev.com.br"
  },
  {
    "prefix": "AL",
    "files": [],
    "email": null
  }
]
```

`email` vem do `user_emails` ativo daquele prefixo. `null` significa prefixo sem email
cadastrado — esse bloco não será enviado.

```bash
curl http://localhost:8000/preview
```

---

## 5. `POST /start`

**A preparação.** Faz o mesmo agrupamento do `/preview`, mas **persiste** como um `Dispatch`
com status `PREPARED` e um `DispatchBlock` por prefixo. Sem body.

Esse é o ponto do sistema inteiro: a partir daqui, o que foi revisado é o que vai sair. Se
alguém mexer na pasta ou trocar um email no cadastro depois do `/start`, a foto não muda.

Cada bloco nasce com `included` calculado — `true` só se tiver email **e** pelo menos um
arquivo. Prefixo sem email ou sem arquivo já vem desmarcado.

**Response `200`**

```json
{
  "id": 109,
  "status": "PREPARED",
  "create_at": "2026-08-18T14:40:00",
  "execute_at": null,
  "finish_at": null,
  "blocks": [
    {
      "id": 3105,
      "prefix_name": "AC",
      "intended_recipient": "ac@sebraeprev.com.br",
      "file_paths": ["C:\\...\\AC.pdf", "C:\\...\\AC.TXT", "C:\\...\\AC.XLSX"],
      "included": true,
      "status": "PENDING",
      "delivered_to": null,
      "delivered_at": null,
      "attempts": 0,
      "error": null
    }
  ],
  "warnings": [],
  "mail_sending_disabled": true,
  "mail_redirected_to": "kaua.santanaj@gmail.com"
}
```

Os blocos vêm ordenados por `prefix_name`.

### O campo `warnings`

Tudo que **não** vai sair, listado pro operador antes de executar:

| aviso | quando |
|---|---|
| `AC: sem email cadastrado, nao sera enviado` | prefixo sem `user_email` ativo |
| `AC: nenhum arquivo encontrado` | bloco vazio |
| `AC: 2 arquivo(s) sumiram da pasta desde a preparacao` | arquivo apagado depois do `/start` |
| `AC: anexos somam 24.3MB, acima do limite de 20MB` | passou do `MAIL_MAX_ATTACHMENT_MB` |
| `2 arquivo(s) fora de qualquer bloco (prefixo nao cadastrado): NA.pdf, SB.pdf` | arquivo órfão |

Os avisos são **recalculados a cada leitura**, não ficam salvos. Por isso o "arquivos
sumiram" só aparece num `GET /dispatch/{id}` posterior, nunca na resposta do próprio `/start`.

⚠️ O aviso de **arquivo órfão** só sai na resposta do `/start`. O `GET /dispatch/{id}` e o
`PATCH` não recebem a lista de `files_without_prefix` e passam `None` pro `PreFlightCheck`.
Se você fechar a aba e reabrir o dispatch, esse aviso some.

```bash
curl -X POST http://localhost:8000/start
```

---

## 6. `GET /dispatch/{id}`

Relê a foto. Mesmo formato do `/start`, com `warnings` recalculados na hora (menos o de
arquivo órfão, ver acima). É aqui que o operador confere antes de mandar executar.

**Erros** — `404` dispatch não existe

```bash
curl http://localhost:8000/dispatch/109
```

---

## 7. `PATCH /dispatch/{id}/block/{block_id}`

A única rota de correção. Serve pra duas coisas: **tirar um bloco do envio** e **trocar o
destinatário** — sem mexer no cadastro global de emails, só nesse dispatch.

**Request** — ambos os campos são opcionais; mande só o que quer mudar

```json
{ "included": false }
```

```json
{ "email": "novo@sebraeprev.com.br" }
```

```json
{ "included": true, "email": "novo@sebraeprev.com.br" }
```

| campo | tipo | nota |
|---|---|---|
| `included` | bool \| null | `null` ou ausente = não altera |
| `email` | EmailStr \| null | normalizado pra minúsculo e sem espaços |

**Response `200`** — o `DispatchResponse` **inteiro**, não só o bloco. Conveniente: você
manda o PATCH e já recebe os `warnings` recalculados com a mudança aplicada.

**Erros** — `404` dispatch ou bloco não existe · `409` dispatch já está `RUNNING` · `422` email inválido

```bash
# tirar o bloco 3118 do envio
curl -X PATCH http://localhost:8000/dispatch/109/block/3118 \
  -H "Content-Type: application/json" \
  -d '{"included":false}'
```

---

## 8. `POST /dispatch/{id}/e  xecute`

**A operação real.** Trava o dispatch (`RUNNING`), devolve `202` na hora e envia em
background via `BackgroundTasks`. Sem body.

> ⚠️ **BUG — a rota tem dois espaços no meio da palavra.** O path declarado em
> [dispatch_controller.py:26](../src/api/dispatch/dispatch_controller.py#L26) é literalmente
> `"/{dispatch_id}/e  xecute"`. Enquanto não for corrigido, o cliente precisa chamar
> `/dispatch/109/e%20%20xecute` — `/dispatch/109/execute` devolve `404`.
> A correção é apagar os dois espaços na string do decorator.

O `202` volta **antes** do envio terminar: `finish_at` ainda é `null` e os blocos ainda estão
`PENDING`. Use o `/status` pra acompanhar.

**Response `202`** — `DispatchResponse` com `status: "RUNNING"` e `execute_at` preenchido.

**Erros**

| status | quando |
|---|---|
| `404` | dispatch não existe |
| `409` | dispatch já está `RUNNING` — a trava contra duplo clique |
| `422` | nenhum bloco enviável (todos `included: false`, sem email, sem arquivo, ou já `SENT`) |

**Reexecutar é seguro:** o `find_blocks_to_send` filtra `status != SENT`, então uma segunda
chamada só reprocessa `PENDING` e `FAILED`. Bloco já entregue nunca sai duas vezes.

```bash
curl -X POST "http://localhost:8000/dispatch/109/e%20%20xecute"
```

---

## 9. `GET /dispatch/{id}/status`

Resposta enxuta pra polling durante o envio. Os contadores são sobre os blocos
**incluídos**; `excluded` é o resto.

**Response `200`**

```json
{
  "id": 109,
  "status": "RUNNING",
  "total": 27,
  "sent": 12,
  "failed": 1,
  "pending": 14,
  "excluded": 2
}
```

| campo | leitura |
|---|---|
| `total` | blocos `included: true` |
| `sent` + `failed` + `pending` | sempre soma `total` |
| `excluded` | blocos tirados do envio |

**Status do dispatch:** `PREPARED` → `RUNNING` → `DONE` (nenhum falhou) ou `PARTIAL`
(pelo menos um `FAILED`).

Quando falha, o motivo fica no `error` de cada bloco, no `GET /dispatch/{id}` — formato
`TipoDoErro: mensagem`, truncado em 2000 caracteres. O `attempts` conta quantas vezes aquele
bloco foi tentado, somando as reexecuções.

**Erros** — `404` dispatch não existe

```bash
curl http://localhost:8000/dispatch/109/status
```

---

## Erros — formato único

Toda exceção de domínio sai no mesmo shape, montado pelo
[exception_handlers.py](../src/api/exception_handlers.py):

```json
{ "detail": "Dispatch is already running" }
```

| `detail` | status |
|---|---|
| `Dispatch not found` | 404 |
| `Dispatch block not found` | 404 |
| `Prefix not found` | 404 |
| `Email  not found` | 404 |
| `Dispatch is already running` | 409 |
| `Prefix already exists` | 409 |
| `Email already exists` | 409 |
| `Dispatch is not ready to be executed` | 422 |
| `Dispatch has no block to send` | 422 |
| `Prefix is required` | 422 |
| `Email  is required` | 422 |

Exceção não mapeada vira `500` com o `str(exception)` no `detail`.

Erro de validação do Pydantic (email malformado, `prefix_name` com 4 letras) também dá `422`,
mas no formato padrão do FastAPI — `detail` é uma **lista** de objetos, não uma string:

```json
{ "detail": [{ "type": "value_error", "loc": ["body", "email"], "msg": "..." }] }
```

Se o cliente for renderizar o `detail` direto na tela, trate os dois casos.

---

## Roteiro completo de um envio

```bash
BASE=http://localhost:8000

# 1. confere os arquivos da pasta, sem gravar nada
curl $BASE/preview

# 2. tira a foto
curl -X POST $BASE/start        # anote o "id" da resposta — ex.: 109

# 3. lê os avisos com calma
curl $BASE/dispatch/109

# 4. tira os blocos que não devem sair
curl -X PATCH $BASE/dispatch/109/block/3118 \
  -H "Content-Type: application/json" -d '{"included":false}'

# 5. corrige um destinatário só nesse dispatch
curl -X PATCH $BASE/dispatch/109/block/3132 \
  -H "Content-Type: application/json" -d '{"email":"novo.sp@sebraeprev.com.br"}'

# 6. envia
curl -X POST "$BASE/dispatch/109/e%20%20xecute"

# 7. acompanha
curl $BASE/dispatch/109/status
```

### No PowerShell

`curl` é alias de `Invoke-WebRequest` no PowerShell 5.1 e **não** aceita essas flags. Use
`curl.exe` explicitamente, ou o cmdlet nativo:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/start" | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Patch -Uri "http://localhost:8000/dispatch/109/block/3118" `
  -ContentType "application/json" -Body '{"included":false}'
```

---

## Um teste seguro, sem torrar a caixa de entrada

Um dispatch completo são 27 emails com 3 anexos cada, todos caindo no mesmo endereço por
causa do `MAIL_REDIRECT_ALL_TO`. Em rajada, vindo de remetente externo, isso vira quarentena.

Comece com 2 ou 3 blocos — depois do `/start`, desmarque o resto:

```bash
for BLOCK in 3106 3107 3108 3109 3110 3111 3112; do
  curl -s -o /dev/null -X PATCH $BASE/dispatch/109/block/$BLOCK \
    -H "Content-Type: application/json" -d '{"included":false}'
done
```

Valide que chegou, que o anexo abre e que o assunto mostra o destinatário real
(`[TESTE -> ac@sebraeprev.com.br] Arquivos AC`). Só depois solte os 27.

---

## O que ainda não tem rota

O CRUD de `UserEmail` existe inteiro — [model](../src/model/user_email/user_email.py),
[repository](../src/repository/user_email/user_email_repository.py),
[service](../src/service/user_email/user_email_service.py) com `create` / `find` / `update` /
`delete`, schemas e exceptions — **mas não tem controller**. O `get_user_email_service` está
declarado em [dependencies.py:17](../src/core/dependencies.py#L17) e nenhum router o injeta.

Na prática: **hoje só dá pra cadastrar email por seed ou direto no banco.** Não existe
`POST /user-email`.

O service já está pronto pra ser exposto; falta o
`src/api/user_email/user_email_controller.py` no mesmo formato dos outros e o `include_router`
no [main.py](../src/main.py).

Enquanto isso, o caminho é o [seed.py](../src/core/seed.py), que popula as 27 UFs e um
`{uf}@sebraeprev.com.br` pra cada:

```bash
python -m src.core.seed
```
