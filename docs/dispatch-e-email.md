# Dispatch e Email — método por método

Guia dos quatro arquivos que fazem o envio funcionar, com os detalhes de Python explicados.
Comparações com Java onde ajuda, já que a versão original era Java.

---

## 1. Por que o nome "dispatch"

`dispatch` em inglês é *despachar / expedir* — o mesmo sentido de transportadora.

A questão central: **precisávamos de um substantivo, não de um verbo.**

Existe uma linha no banco, com `id`, `status` e data. Essa linha é uma *coisa*, que você pode
consultar (`GET /dispatch/3`), listar e auditar. `enviar` é ação; não se guarda ação numa
tabela, se guarda o **registro** da ação.

E o verbo já estava ocupado. Repare:

```python
class DispatchSender:
    async def send(self, dispatch_id: int) -> None:
```

`Dispatch` é o substantivo (a expedição), `send` é o verbo (expedir). Se a entidade fosse
chamada `Send` ou `Envio`, você acabaria com `SendService.send()` — que não diz nada.

Também importa a **escala**. Um `dispatch` não é um email, é **uma rodada inteira de
distribuição**: 27 blocos, cada um com 3 arquivos e 1 destinatário. Na analogia da
transportadora:

| transportadora | aqui |
|---|---|
| uma expedição (um caminhão saindo) | `Dispatch` |
| cada pacote dentro dela | `DispatchBlock` |
| a etiqueta do pacote | `intended_recipient` |
| quem assinou o recebimento | `delivered_to` |

### O que foi considerado e descartado

| nome | por que não |
|---|---|
| `Envio` | mistura português no meio de um código todo em inglês |
| `Batch` | genérico demais — batch de quê? |
| `Distribution` | longo, e "distribuição" já é o nome do projeto todo |
| `Send` | verbo; e colidia com o método `send()` |

---

## 2. Quem chama quem

```
POST /start                     ──> DispatchService.prepare()
                                       └─> PreparationService  (monta os blocos)
                                       └─> PreFlightCheck      (gera os avisos)

PATCH /dispatch/1/block/5       ──> DispatchService.update_block()

POST /dispatch/1/execute        ──> DispatchService.lock_for_execution()   [na requisição]
                                └─> send_dispatch()                        [em background]
                                       └─> DispatchSender.send()
                                              └─> MailService.send_files()
```

O ponto: `DispatchService` **nunca** envia email, e `DispatchSender` **nunca** valida
permissão. Um cuida de estado, o outro de entrega.

---

## 3. `DispatchService` — o dono do estado

Arquivo: [`src/service/dispatch/dispatch_service.py`](../src/service/dispatch/dispatch_service.py)

### `prepare()`

É o `/start`. Tira a foto.

```python
def prepare(self) -> DispatchResponse:
    file_blocks = self.preparation_service.mount_block_files()
    files_without_prefix = self.preparation_service.find_files_without_prefix(file_blocks)

    dispatch = Dispatch()
    dispatch.status = DispatchStatus.PREPARED
    dispatch.create_at = datetime.now()
    dispatch.blocks = [self._to_block(file_block) for file_block in file_blocks]

    self.dispatch_repository.save(dispatch)

    return self._to_response(dispatch, files_without_prefix)
```

1. pede os blocos pro `PreparationService` (que lê a pasta e o cadastro)
2. pergunta quais arquivos ficaram de fora
3. cria o `Dispatch` com status `PREPARED`
4. converte cada `FileBlock` (objeto de memória) em `DispatchBlock` (linha de banco)
5. salva — o SQLAlchemy grava o pai **e** os filhos numa tacada, por causa do
   `cascade="all, delete-orphan"` no model

> **Python:** `[self._to_block(fb) for fb in file_blocks]` é *list comprehension* —
> equivale ao `.stream().map(...).toList()` do Java, mas é sintaxe da linguagem, não
> biblioteca. Lê-se de dentro pra fora: "pra cada `fb` em `file_blocks`, me dá
> `self._to_block(fb)`".

### `find_dispatch(dispatch_id)`

É o `GET /dispatch/{id}`. Busca e converte pra resposta.

```python
def find_dispatch(self, dispatch_id: int) -> DispatchResponse:
    return self._to_response(self._get_dispatch(dispatch_id))
```

> **Detalhe honesto:** aqui o `_to_response` é chamado **sem** o segundo argumento, então
> os avisos de arquivo órfão (`NA.*`, `SB.*`) **não** aparecem — só os avisos por bloco.
> Aqueles órfãos só são calculados no `/start`, porque descobri-los exige reler a pasta.
> Se você quiser que apareçam no `GET` também, é passar o segundo argumento aqui.

### `update_block(dispatch_id, block_id, request)`

É o `PATCH`. O operador tira um bloco ou troca o destinatário.

```python
if dispatch.is_running:
    raise DispatchAlreadyRunningException()

block = self._get_block(dispatch, block_id)

if request.included is not None:
    block.included = request.included

if request.email is not None:
    block.intended_recipient = request.email.strip().lower()
```

O `is not None` é importante: os dois campos são opcionais no request. Mandar
`{"included": false}` só mexe no `included` e deixa o email quieto. Se o teste fosse
`if request.included:`, mandar `false` não faria nada — porque `False` é "falsy".

> **Python:** `strip().lower()` = `trim().toLowerCase()`. Normalizar na entrada evita
> `SP@x.com` e `sp@x.com` virarem dois cadastros.

### `lock_for_execution(dispatch_id)`

O guarda do `/execute`. **Não envia nada** — só decide se pode enviar e tranca.

```python
if dispatch.is_running:
    raise DispatchAlreadyRunningException()      # -> HTTP 409

if not self._sendable_blocks(dispatch_id):
    raise DispatchNothingToSendException()       # -> HTTP 422

dispatch.status = DispatchStatus.RUNNING
dispatch.execute_at = datetime.now()
dispatch.finish_at = None
```

Duas travas:

- **já rodando** → 409. É isso que impede duplo clique de mandar tudo duas vezes.
- **nada pra enviar** → 422. Ou tudo já foi, ou todos os blocos estão excluídos.

O `finish_at = None` limpa a data da rodada anterior — importa no retry, senão um dispatch
`PARTIAL` reexecutado ficaria com data de término mais antiga que o novo início.

É síncrono e rápido de propósito: precisa responder na requisição HTTP.

### `find_status(dispatch_id)`

O placar, pro front ficar consultando.

```python
sent=self._count(included, BlockStatus.SENT),
failed=self._count(included, BlockStatus.FAILED),
pending=self._count(included, BlockStatus.PENDING),
excluded=len(dispatch.blocks) - len(included),
```

`excluded` é o total menos os incluídos — os blocos que o operador desmarcou.

### Os privados

| método | o que faz |
|---|---|
| `_to_block(file_block)` | `FileBlock` (memória) → `DispatchBlock` (banco). Já marca `included=False` se o bloco não tem email ou não tem arquivo |
| `_to_response(dispatch, files_without_prefix)` | monta o JSON, chamando o `PreFlightCheck` pros avisos |
| `_count(blocks, status)` | conta quantos blocos estão num status |
| `_sendable_blocks(id)` | pergunta ao repository e filtra por `is_sendable` |
| `_get_dispatch(id)` | busca ou levanta `DispatchNotFoundException` |
| `_get_block(dispatch, id)` | acha o bloco na lista ou levanta exception |

> **Python — o `_` no início:** é só convenção, "não use isso de fora". Não existe `private`
> de verdade; nada te impede de chamar `service._get_block(...)`. A linguagem confia em você.

> **Python — o `next(...)`:**
> ```python
> block = next((block for block in dispatch.blocks if block.id == block_id), None)
> ```
> É o `.stream().filter(...).findFirst().orElse(null)` do Java. O parêntese interno é um
> *generator* (avalia sob demanda, para no primeiro achado) e o `None` é o valor de fallback.
> **Sem** esse `None`, se não achar nada ele estoura `StopIteration` em vez de devolver nada.

---

## 4. `DispatchSender` — o dono da entrega

Arquivo: [`src/service/dispatch/dispatch_sender.py`](../src/service/dispatch/dispatch_sender.py)

Esse é o arquivo mais estranho do projeto, e vale entender por quê: ele roda **fora** da
requisição HTTP, num mundo `async`, enquanto o resto do projeto é síncrono.

### `send(dispatch_id)`

```python
async def send(self, dispatch_id: int) -> None:
    with new_session() as session:
        repository = DispatchRepository(session)

        for block in await self._in_database(repository.find_blocks_to_send, dispatch_id):
            await self._send_block(block)
            await self._in_database(repository.save_block, block)

        await self._finish(repository, dispatch_id)
```

Três decisões embutidas aqui:

**1. Sessão própria (`new_session()`).** A sessão que o FastAPI injeta via
`Depends(get_db)` é fechada quando a resposta HTTP sai. Esse código roda **depois** disso.
Reaproveitar aquela sessão dá `DetachedInstanceError`.

**2. Salva bloco por bloco, dentro do loop.** Cada `save_block` faz commit. Se o décimo
email falhar, os nove primeiros já estão gravados como `SENT` e não serão reenviados. Se
salvasse tudo no final, uma falha no meio apagaria o registro do que já tinha saído — e o
retry mandaria de novo pra quem já recebeu.

**3. Sequencial.** Um bloco por vez. Servidor SMTP corporativo derruba conexão se você
disparar 27 em paralelo.

> **Python — `with`:** é o `try-with-resources` do Java. `new_session()` é um
> *context manager*: abre a sessão, entrega pro bloco, e fecha **mesmo se der exception**.

> **Python — `async`/`await`:** `async def` cria uma função que precisa ser esperada com
> `await`. Diferente de thread do Java: é **um único thread** que troca de tarefa a cada
> `await`. Por isso travar nele congela a aplicação toda — veja `_in_database` abaixo.

### `_send_block(block)`

O envio de um bloco, com o `try/except` que decide `SENT` ou `FAILED`.

```python
if not block.is_sendable:
    return

block.attempts += 1

try:
    block.delivered_to = await self.mail_service.send_files(
        block.prefix_name, block.intended_recipient, block.files
    )
    block.status = BlockStatus.SENT
    block.delivered_at = datetime.now()
    block.error = None
except Exception as error:
    block.status = BlockStatus.FAILED
    block.error = self._describe(error)
```

- `attempts += 1` vem **antes** do `try`: a tentativa conta mesmo se falhar.
- `error = None` no sucesso: limpa o erro da tentativa anterior num retry.
- `delivered_to` recebe o que o `MailService` devolveu — quem **de fato** recebeu, que é
  diferente do `intended_recipient` quando a trava de redirecionamento está ligada.

> **Python:** `except Exception as error` = `catch (Exception error)`. Pegar `Exception`
> genérico normalmente é ruim, mas aqui é intencional: qualquer falha num bloco não pode
> derrubar os outros 26.

### `_finish(repository, dispatch_id)`

Fecha o dispatch depois do loop: decide `DONE` ou `PARTIAL` e grava `finish_at`.

### `_final_status(dispatch)`

```python
if dispatch.failed_blocks:
    return DispatchStatus.PARTIAL
return DispatchStatus.DONE
```

> **Python:** `if dispatch.failed_blocks:` — lista vazia é `False`, lista com algo é `True`.
> Não precisa de `.isEmpty()`. Mesma ideia com string vazia, dict vazio e `0`.

### `_describe(error)`

```python
return f"{type(error).__name__}: {error}"[:MAX_ERROR_LENGTH]
```

Vira `"WrongFile: incorrect file path for attachment"`, cortado em 2000 caracteres pra
caber na coluna `error`.

> **Python:** `f"..."` é *f-string* — interpolação, como `"%s".formatted()` mas embutido.
> `[:2000]` é *slicing*: os primeiros 2000 caracteres. Não estoura se a string for menor.

### `_in_database(operation, *args)`

O método mais importante do arquivo:

```python
@staticmethod
async def _in_database(operation: Callable[..., Any], *args: Any) -> Any:
    return await run_in_threadpool(operation, *args)
```

**O problema que ele resolve:** os repositories usam SQLAlchemy **síncrono**. Se você chamar
`repository.save_block(block)` direto dentro de uma função `async`, o event loop **para** e
espera o MySQL responder — e como é um thread só, a aplicação inteira congela nesse tempo.
Multiplique por 27 blocos e o app fica travado por dezenas de segundos.

`run_in_threadpool` joga a chamada síncrona pra outra thread e devolve um `await`. O loop
fica livre pra atender outras requisições.

Por isso todo acesso a banco aqui vira `await self._in_database(repository.metodo, arg)`.

> **Python — `*args`:** aceita qualquer quantidade de argumentos posicionais e junta numa
> tupla, tipo `Object... args` do Java. Repassar com `*args` "desempacota" de volta.
> Repare que se passa a **função sem chamar** (`repository.save_block`, sem parênteses) —
> em Python função é valor, como um `Runnable`.

### `send_dispatch(dispatch_id)`

```python
async def send_dispatch(dispatch_id: int) -> None:
    await DispatchSender().send(dispatch_id)
```

Função solta no fim do arquivo, fora da classe. Existe porque o
`background_tasks.add_task()` do FastAPI quer receber uma função simples, e assim o
controller não precisa saber que existe uma classe `DispatchSender`.

---

## 5. `MailService` — o dono do email

Arquivo: [`src/service/mail/mail_service.py`](../src/service/mail/mail_service.py)

### `connection_config` (fora da classe)

```python
connection_config = ConnectionConfig(
    ...
    SUPPRESS_SEND=1 if settings.MAIL_SENDING_DISABLED else 0,
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)
```

Roda **uma vez**, quando o módulo é importado. `SUPPRESS_SEND=1` é a trava 1: o
fastapi-mail monta a mensagem e não conecta no SMTP.

> **Python:** `1 if condicao else 0` é o ternário — a ordem é invertida em relação ao
> Java (`condicao ? 1 : 0`). Valor primeiro, condição depois.

### `send_files(prefix_name, intended_recipient, files)`

O único método público de verdade.

```python
async def send_files(self, prefix_name: str, intended_recipient: str, files: list[Path]) -> str:
    actual_recipient = self.actual_recipient_for(intended_recipient)
    message = self._build_message(prefix_name, intended_recipient, actual_recipient, files)

    await self.mail.send_message(message, template_name=self.TEMPLATE_NAME)

    return actual_recipient
```

A **ordem** das duas primeiras linhas é intencional, e é a correção de um bug real: antes eu
montava a mensagem e depois lia o destinatário de volta dela, com
`return message.recipients[0]`. O problema é que o fastapi-mail converte `recipients` num
objeto `NameEmail`, não numa string — e isso ia direto pra coluna `delivered_to`, que é
`String(255)`.

Resolvendo o destinatário **primeiro** e devolvendo essa variável, o retorno é
garantidamente `str` e o caminho errado deixa de existir.

### `actual_recipient_for(intended_recipient)`

```python
@staticmethod
def actual_recipient_for(intended_recipient: str) -> str:
    return settings.MAIL_REDIRECT_ALL_TO or intended_recipient
```

Três linhas, e é **a trava de segurança inteira**. Se `MAIL_REDIRECT_ALL_TO` está
preenchido, todo email vai pra lá; se está vazio, vai pro destinatário real.

Está isolado num método por um motivo: é o **único** ponto do código que decide destinatário.
Não existe caminho que mande email pulando ele.

> **Python — `or` devolve valor, não booleano:** `a or b` devolve `a` se `a` for
> "truthy", senão devolve `b`. String vazia é falsy, então
> `"" or "sp@x.com"` → `"sp@x.com"`. É o idioma padrão de "valor com fallback", tipo o
> `Optional.orElse()`.

### `_build_message(...)` e `_build_subject(...)`

Montam o `MessageSchema` (destinatário, corpo, anexos) e o assunto. Quando a trava está
ligada, o assunto ganha o prefixo `[TESTE -> sp@sebraeprev.com.br]` — assim, olhando a
caixa de entrada, você sabe pra quem **iria** cada email.

O `template_body` é o dicionário que vai pro Jinja2. As chaves viram variáveis no
`dispatch_email.html`: `{{ prefix_name }}`, `{% for file_name in file_names %}`.

---

## 6. `PreFlightCheck` — o dono dos avisos

Arquivo: [`src/service/dispatch/pre_flight_check.py`](../src/service/dispatch/pre_flight_check.py)

Uma responsabilidade só: responder "o que vai dar errado se executar agora?". Não corrige,
não bloqueia, não salva — devolve `list[str]` pro operador ler.

### `__init__(dispatch, files_without_prefix=None)`

```python
self.files_without_prefix = files_without_prefix or []
```

> **Python — pegadinha clássica:** o default é `None`, não `[]`. Escrever
> `def __init__(self, files=[])` é bug em Python: a lista é criada **uma vez**, na definição
> da função, e **compartilhada entre todas as chamadas**. Se um objeto adicionar item nela,
> o próximo objeto já nasce com o item. O padrão é sempre `=None` e depois `or []`.

### `warnings()`

```python
block_warnings = [
    warning
    for block in sorted(self.dispatch.included_blocks, key=lambda block: block.prefix_name)
    for warning in self._warnings_for(block)
]
return block_warnings + self._warnings_for_files_without_prefix()
```

> **Python — comprehension aninhada:** os dois `for` se leem **na ordem em que aparecem**,
> como se fossem aninhados:
> ```python
> for block in sorted(...):
>     for warning in self._warnings_for(block):
>         adiciona warning
> ```
> É o `flatMap`: cada bloco pode gerar 0, 1 ou 4 avisos, e o resultado é uma lista plana.

> **Python — `sorted(key=lambda ...)`:** `key` recebe uma função que extrai o valor de
> comparação. Igual ao `Comparator.comparing(Block::getPrefixName)`.

### `_warnings_for(block)`

```python
checks = (
    self._missing_recipient(block),
    self._empty_block(block),
    self._vanished_files(block),
    self._oversized_attachments(block),
)
return [warning for warning in checks if warning is not None]
```

Roda as quatro verificações e joga fora as que não tinham nada a dizer.

O contrato de cada uma é: **devolve `str` se tem problema, `None` se está tudo bem.**
Adicionar uma regra nova é escrever um método e somar uma linha na tupla — não é mexer
num método de 40 linhas.

> **Python — `str | None`:** é o `Optional<String>` do Java, mas o `|` é união de tipos.
> `str | None` = "ou uma string, ou nada". E **type hint em Python não é validado em
> tempo de execução** — é documentação pra você e pra IDE. Nada impede devolver um `int` ali.

### As quatro verificações

| método | pergunta |
|---|---|
| `_missing_recipient` | esse prefixo tem email cadastrado? |
| `_empty_block` | achou algum arquivo pra esse prefixo? |
| `_vanished_files` | os arquivos congelados no `/start` ainda existem na pasta? |
| `_oversized_attachments` | a soma dos anexos passa do limite de MB? |

O `_vanished_files` é o que protege contra a pasta mudar entre a preparação e o envio —
o motivo de existir a foto.

```python
total_bytes = sum(file.stat().st_size for file in block.files if file.exists())
```

> **Python — generator expression:** sem colchetes, dentro do `sum()`. Igual a uma list
> comprehension, mas não constrói a lista na memória — vai somando. O `if file.exists()`
> filtra: arquivo que sumiu não tem tamanho, e chamar `.stat()` nele estouraria.

---

## 7. Cola rápida Java → Python

Tudo isso aparece nos arquivos acima.

| Python | Java | nota |
|---|---|---|
| `str \| None` | `Optional<String>` | hint, não validado em runtime |
| `[f(x) for x in lista]` | `.stream().map(f).toList()` | sintaxe da linguagem |
| `[x for x in lista if cond]` | `.stream().filter(...)` | |
| `{k: v for x in lista}` | `Collectors.toMap` | dict comprehension |
| `sum(x for x in lista)` | `.mapToInt().sum()` | generator, não cria lista |
| `next((x for x in l if c), None)` | `.findFirst().orElse(null)` | **sempre** passe o `None` |
| `a or b` | `Optional.orElse` | devolve valor, não booleano |
| `if not lista:` | `if (lista.isEmpty())` | vazio é falsy |
| `with recurso() as r:` | try-with-resources | fecha mesmo com exception |
| `@property` | getter | chama **sem** parênteses: `block.is_sendable` |
| `@staticmethod` | `static` | não recebe `self` |
| `f"oi {nome}"` | `"oi %s".formatted(nome)` | f-string |
| `texto[:100]` | `substring(0, 100)` | não estoura se for menor |
| `*args` | `Object... args` | vira tupla |
| `_metodo` | `private` | só convenção, não é bloqueado |
| `1 if c else 0` | `c ? 1 : 0` | ordem invertida |
| `def f(x=None)` + `x or []` | — | **nunca** `def f(x=[])` |

### `@property`, que aparece muito no model

```python
@property
def is_sendable(self) -> bool:
    return self.included and self.intended_recipient is not None and bool(self.file_paths)
```

Chama-se como atributo: `block.is_sendable`, **sem** parênteses. É um getter que parece
campo. Serve pra dar nome a uma condição — comparar `if block.is_sendable:` com repetir
`if block.included and block.intended_recipient is not None and ...` em quatro lugares.

Os do projeto: `is_sendable`, `was_sent`, `included_blocks`, `failed_blocks`, `is_running`.

### `StrEnum`, nos status

```python
class BlockStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
```

`StrEnum` é enum **que também é string**. Então `BlockStatus.SENT == "SENT"` é `True`, e o
SQLAlchemy grava direto na coluna `String(20)` sem conversão. Você ganha autocomplete e
proteção contra typo (`BlockStatus.SETN` explode na hora; `"SETN"` passaria calado).
