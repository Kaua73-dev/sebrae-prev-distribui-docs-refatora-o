from fastapi import FastAPI
from src.api.prefix.prefix_controller import router as prefix_router

app = FastAPI(title="Distribui Docs API")

app.include_router(prefix_router)
