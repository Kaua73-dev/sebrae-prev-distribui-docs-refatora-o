# Sebrae Prev automatização de documentos patrocinadoras

Código de refatoração do projeto feito em java e implementação de novas features.

---

> Detalhamento método por método do envio, com o Python explicado:
> [`docs/dispatch-e-email.md`](docs/dispatch-e-email.md)

## O que o sistema faz

Lê uma pasta com arquivos nomeados por prefixo de estado (`SP.pdf`, `SP.TXT`, `SP.XLSX`, `RJ.pdf`...),
agrupa em blocos por prefixo e envia cada bloco por email para o destinatário daquele prefixo.

## O fluxo

```
POST /start                              PREPARAÇÃO: tira uma "foto" e salva no banco
GET  /dispatch/{id}                      operador confere os blocos e os avisos
PATCH /dispatch/{id}/block/{block_id}    operador tira blocos / troca emails
POST /dispatch/{id}/execute              OPERAÇÃO REAL: envia (202, roda em background)
GET  /dispatch/{id}/status               acompanha o progresso
GET  /preview                            só olhar os blocos, sem gravar nada
```

### Por que "tirar uma foto"

O `/start` monta os blocos **uma vez** e congela no banco (`dispatch` + `dispatch_block`):
prefixo, destinatário e a lista de caminhos dos arquivos.

O `/execute` **não remonta nada** — lê o que foi congelado.

Isso existe porque entre a preparação e o envio a realidade pode mudar: alguém mexe na pasta,
alguém edita um email no cadastro, um prefixo é desativado. Sem a foto, o operador aprova
uma lista e o sistema envia outra — arquivo do PR indo pro email do SP, sem ninguém notar.

| | |
|---|---|
| **Sem drift** | o que foi revisado é o que sai |
| **Retry seguro** | reexecutar só reenvia bloco `FAILED`/`PENDING`, nunca um `SENT` |
| **Idempotência** | duplo clique no execute bate em `409`, não manda tudo duas vezes |
| **Auditoria** | quem recebeu o quê, quando, com quantas tentativas |

## As duas travas de segurança

Configuradas no `.env` (veja `.env.example`). **As duas vêm ligadas por padrão.**

```env
MAIL_SENDING_DISABLED=True
MAIL_REDIRECT_ALL_TO=seu.email@gmail.com
```

- **`MAIL_SENDING_DISABLED=True`** — monta a mensagem e para aí, não conecta no SMTP.
- **`MAIL_REDIRECT_ALL_TO`** — se preenchido, **todo** email vai pra esse endereço em vez do
  destinatário real. O destinatário real continua em `dispatch_block.intended_recipient`,
  aparece no assunto (`[TESTE -> sp@sebraeprev.com.br] Arquivos SP`) e no corpo.
  A auditoria não mente: `dispatch_block.delivered_to` registra quem **de fato** recebeu.

Enquanto qualquer uma estiver ativa, a resposta do `/start` avisa em `mail_sending_disabled`
e `mail_redirected_to`. Para enviar de verdade: `MAIL_SENDING_DISABLED=False` e
`MAIL_REDIRECT_ALL_TO=` (vazio).

## Avisos de pré-voo

O `/start` devolve `warnings[]` com tudo que **não** vai sair, pro operador ver antes de executar:

- prefixo sem email cadastrado
- bloco sem nenhum arquivo
- arquivo que sumiu da pasta desde a preparação
- anexos acima de `MAIL_MAX_ATTACHMENT_MB`
- **arquivos órfãos**: estão na pasta mas o prefixo não existe no cadastro. Hoje são os
  `NA.*` e `SB.*`. Antes desse aviso eles desapareciam calados.

## Status

| `dispatch.status` | |
|---|---|
| `PREPARED` | foto tirada, esperando revisão/execução |
| `RUNNING` | enviando (bloqueia nova execução) |
| `DONE` | todos os incluídos enviados |
| `PARTIAL` | terminou com falhas — reexecutar tenta só elas |

| `dispatch_block.status` | |
|---|---|
| `PENDING` | ainda não enviado |
| `SENT` | enviado (nunca é reenviado) |
| `FAILED` | falhou, veja a coluna `error` |

## Tabelas

```
dispatch         id, status, create_at, execute_at, finish_at
dispatch_block   id, dispatch_id, prefix_name, intended_recipient, file_paths (JSON),
                 included, status, delivered_to, delivered_at, attempts, error
```

`prefix` e `user_emails` vêm da versão Java (Hibernate) e continuam como estavam.
`user_emails.email` tem `UNIQUE (uk_user_email)` — um email atende no máximo um prefixo.

Criadas com `Base.metadata.create_all(engine)`, que só cria o que falta.

## Rodando

```bash
docker compose -f Docker-compose.yml up -d      # MySQL
python -m src.core.seed                          # 27 prefixos + 1 email por prefixo
uvicorn src.main:app --reload                    # API em /docs
```

---

# Por que cada service existe

Cada um tem uma razão única para mudar. Se dois motivos diferentes fariam você editar o mesmo
arquivo, ele deveria ter sido dois.

### `PrefixService`
**Dono do cadastro de prefixos.** Sabe que prefixo é sempre maiúsculo e sem espaço, que não
pode duplicar, e quais estão marcados como obrigatórios. É o único lugar que decide
"esse prefixo entra na distribuição?" (`find_prefix_required_true`).

*Muda quando:* a regra de nome ou de obrigatoriedade do prefixo mudar.

### `UserEmailService`
**Dono do cadastro de destinatários.** Normaliza email (`strip` + `lower`), garante que um
email atende no máximo um prefixo, e liga email a prefixo. É o cadastro base — a fonte de
onde o `/start` vai copiar.

*Muda quando:* a regra de quem pode receber mudar.

### `PreparationService`
**Traduz pasta de arquivos em blocos.** É o único que conhece o disco: sabe que extensão
aceita, e sabe a regra de que `SP.pdf` pertence ao prefixo `SP` mas `SPA.pdf` não
(o caractere após o prefixo não pode ser letra). Junta com o email de cada prefixo e devolve
`FileBlock`. Também aponta o que ficou de fora (`find_files_without_prefix`).

*Muda quando:* a convenção de nome dos arquivos ou as extensões aceitas mudarem.

Ele **não** persiste nada e **não** envia nada. É uma função pura sobre disco + cadastro,
por isso o `/preview` pode chamar ele à vontade sem efeito colateral.

### `DispatchService`
**Dono do ciclo de vida do envio.** É o único que escreve em `dispatch`/`dispatch_block`.
Faz quatro coisas: congela a foto (`prepare`), deixa o operador revisar (`update_block`),
trava contra duplo clique (`lock_for_execution`) e conta o progresso (`find_status`).

*Muda quando:* o fluxo de aprovação mudar (ex.: exigir dois aprovadores).

Ele **não** envia email. Separado do envio de propósito: a decisão "isso está pronto pra
sair?" é síncrona, rápida e precisa responder na requisição HTTP. O envio é lento e
assíncrono. Juntar os dois obrigaria o operador a esperar 27 conexões SMTP com o browser
aberto.

### `PreFlightCheck`
**Só responde "o que vai dar errado se executar agora?".** Não corrige, não bloqueia, não
persiste — devolve uma lista de avisos em português pro operador ler.

*Muda quando:* aparecer uma validação nova.

É classe separada porque validação cresce sem parar. Cada regra é um método pequeno
(`_missing_recipient`, `_vanished_files`, `_oversized_attachments`) e uma regra nova é um
método novo, não um `if` no meio de um método de 40 linhas.

### `MailService`
**Dono do email como artefato.** Monta assunto, corpo Jinja2 e anexos, e é o **único lugar**
que aplica o `MAIL_REDIRECT_ALL_TO`. Isso é intencional: a trava de segurança tem um só ponto
de entrada, então não existe caminho no código que mande email pulando ela.

*Muda quando:* o template, o assunto ou o provedor de email mudarem.

Recebe o `FastMail` pelo construtor, o que permite testar com `record_messages()` sem
tocar em SMTP.

### `DispatchSender`
**Dono do envio em si**, e da ponte entre o mundo async e o síncrono. Percorre os blocos,
chama o `MailService`, e grava `SENT`/`FAILED` bloco por bloco — commit a cada um, para que
uma falha no décimo não apague os nove que já foram.

*Muda quando:* a estratégia de envio mudar (paralelismo, retry automático, fila).

Está separado do `DispatchService` por causa do async, e porque roda **fora** da requisição
HTTP: ele abre a própria sessão de banco (a do `Depends(get_db)` já fechou quando a resposta
saiu) e passa todo acesso ao banco por `_in_database`, que joga a chamada síncrona do
SQLAlchemy numa threadpool. Sem isso, o event loop congelaria a aplicação inteira enquanto
o SMTP responde.

O envio é **sequencial** de propósito: servidor SMTP corporativo rate-limita e derruba
conexão se você disparar 27 de uma vez.

---

### Detalhe de ambiente

MySQL é `REPEATABLE READ`: uma sessão de vida longa não vê commits de outras sessões até
encerrar a transação. Não afeta a API (cada request abre sessão nova), mas atrapalha em
script — se um `SELECT` parece desatualizado, falta um `rollback()`.
