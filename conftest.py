"""
Configuracao que roda ANTES de qualquer teste.

Este arquivo existe na raiz do projeto por dois motivos tecnicos:

1. sys.path — a presenca de um conftest.py na raiz faz o pytest colocar a raiz do
   projeto no sys.path. Sem isso, "from src.core.config import settings" dentro de
   tests/ estoura ModuleNotFoundError.

2. Variaveis de ambiente — src/core/config.py executa "settings = Settings()" no
   momento do import, e sete campos sao obrigatorios. Se o ambiente nao estiver
   preenchido ANTES desse import, o teste nem chega a rodar: morre com ValidationError.
   O pytest carrega o conftest.py antes dos modulos de teste, entao aqui e o unico
   lugar que funciona.

Por isso este arquivo NAO pode importar nada de src no topo.
"""

import os

# --------------------------------------------------------------------------------------
# Valores so para satisfazer a validacao do Settings. Nenhum teste conecta neste banco.
# setdefault: se voce ja tiver a variavel no ambiente, a sua vence.
# --------------------------------------------------------------------------------------
os.environ.setdefault("APP_NAME", "distribui-docs-test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "distribui_docs_test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_ECHO", "false")

# --------------------------------------------------------------------------------------
# Travas de seguranca. Aqui e atribuicao direta, NAO setdefault — de proposito.
#
# Se fosse setdefault e voce tivesse MAIL_SENDING_DISABLED=False no seu ambiente,
# a sua variavel venceria e a suite mandaria email de verdade para patrocinador.
# Estas quatro linhas sao a unica coisa que garante que rodar pytest nunca envia nada.
#
# MAIL_SENDING_DISABLED e lida no import de mail_service.py (vira SUPPRESS_SEND=1),
# e com SUPPRESS_SEND=1 o fastapi-mail nunca chama .connect() no servidor SMTP.
# --------------------------------------------------------------------------------------
os.environ["MAIL_SENDING_DISABLED"] = "True"
os.environ["MAIL_REDIRECT_ALL_TO"] = ""
os.environ["MAIL_HOST"] = ""
os.environ["MAIL_USERNAME"] = ""
os.environ["MAIL_PASSWORD"] = ""

# --------------------------------------------------------------------------------------
# Pasta de arquivos: aponta para um caminho que nao existe, de proposito.
# Assim, um teste que esquecer de trocar isso falha na hora em vez de ler (ou pior,
# anexar) os arquivos reais de producao.
# --------------------------------------------------------------------------------------
os.environ["FILES_DIR_PATH"] = os.path.join(os.path.dirname(__file__), "_pasta_inexistente_de_teste")
