from contextlib import asynccontextmanager

from fastapi import FastAPI

from .prisma import prisma
from .routes import auth, posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    print("✅ Database connected")
    yield
    await prisma.disconnect()
    print("✅ Database disconnected")


app = FastAPI(lifespan=lifespan, title="Noo Blog API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Noo Blog API 🚀"}
