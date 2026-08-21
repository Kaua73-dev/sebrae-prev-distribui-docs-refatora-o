from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dispatch.dispatch_controller import router as dispatch_router
from src.api.exception_handlers import register_exception_handlers
from src.api.prefix.prefix_controller import router as prefix_router
from src.api.preparation.preparation_controller import router as preparation_router
from src.api.user.user_controller import router as user_router
from src.api.user_email.user_email_controller import router as user_email_router
from src.core.config import settings
from src.core.dependencies import get_current_user

app = FastAPI(title="Distribui Docs API")

# Token no header Authorization (nao cookie), entao allow_credentials fica desligado
# e CORS_ORIGINS="*" funciona em desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /auth e o unico router aberto — o proprio login mora nele.
app.include_router(user_router)

# Todo o resto exige token. A protecao fica aqui, no include_router, para que nenhum
# controller precise repetir a dependency em cada rota.
PROTECTED = Depends(get_current_user)

app.include_router(prefix_router, dependencies=[PROTECTED])
app.include_router(user_email_router, dependencies=[PROTECTED])
app.include_router(preparation_router, dependencies=[PROTECTED])
app.include_router(dispatch_router, dependencies=[PROTECTED])

register_exception_handlers(app)
