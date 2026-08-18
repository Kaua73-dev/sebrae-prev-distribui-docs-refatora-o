from fastapi import FastAPI

from src.api.dispatch.dispatch_controller import router as dispatch_router
from src.api.exception_handlers import register_exception_handlers
from src.api.prefix.prefix_controller import router as prefix_router
from src.api.preparation.preparation_controller import router as preparation_router
from src.api.user_email.user_email_controller import router as user_email_router

app = FastAPI(title="Distribui Docs API")

app.include_router(prefix_router)
app.include_router(user_email_router)
app.include_router(preparation_router)
app.include_router(dispatch_router)

register_exception_handlers(app)
