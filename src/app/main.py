from fastapi import FastAPI, Depends  # <-- added Depends here
from contextlib import asynccontextmanager
from pydantic import SecretStr
from fastauth import FastAuth, FastAuthOptions
from fastauth.providers.email import EmailProvider
from .config import settings
from .prisma import prisma
from .adapters.prisma_adapter import PrismaAdapter
from .dependencies import require_auth
from prisma.models import User
from .routes import posts

# ---------- FastAuth Setup (must be before lifespan) ----------
adapter = PrismaAdapter(prisma)

options = FastAuthOptions(
    secret_key=SecretStr(settings.FASTAUTH_SECRET),
    database=adapter,
    providers=[EmailProvider()],
    access_token_expires_in=60 * 60 * 24 * 7,  # 7 days
)

auth = FastAuth(options, plugins=[])


# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    print("✅ Database connected")
    # Now auth is defined
    async with auth.lifespan(app):
        yield
    await prisma.disconnect()
    print("✅ Database disconnected")


# ---------- FastAPI App ----------
app = FastAPI(lifespan=lifespan, title="Noo Blog API")

# Include auth routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
auth.add_middleware(app)


# ---------- Root endpoint ----------
@app.get("/")
async def root():
    return {"message": "Noo Blog API 🚀"}


# ---------- Protected endpoint ----------
@app.get("/protected")
async def protected_route(user: User = Depends(require_auth)):  # noqa: B008
    return {"message": f"Hello {user.full_name}", "user_id": user.id}


# ---------- Include your app routes ----------
app.include_router(posts.router, prefix="/api/v1")
