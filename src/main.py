from fastapi import FastAPI
from src.api.prefix.prefix_controller import router as prefix_router
from src.api.preparation.preparation_controller import router as preparation_router



app = FastAPI(title="Distribui Docs API")

app.include_router(prefix_router)
app.include_router(preparation_router)