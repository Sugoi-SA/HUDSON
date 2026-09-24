from fastapi import FastAPI

from app.routers import health, items, search

app = FastAPI(title="HUDSON S1 - API v0")

app.include_router(health.router)
app.include_router(search.router)
app.include_router(items.router)
