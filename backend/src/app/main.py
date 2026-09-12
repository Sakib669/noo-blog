# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
# Responsibilities:
#   1. Manage the Prisma client lifecycle (connect on startup, disconnect
#      on shutdown) via FastAPI's `lifespan` context manager.
#   2. Create the FastAPI app instance.
#   3. Mount all routers under the /api/v1 prefix.
#   4. Define any top-level routes (like `/`).
#
# Run with:
#   uv run uvicorn src.app.main:app --reload
# ---------------------------------------------------------------------------

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager
# asynccontextmanager → turns an async generator into an object usable
# with `async with`, which FastAPI uses for the lifespan hook.

from fastapi import FastAPI
# The web framework class. One instance = one ASGI app.

from .prisma import prisma
# Single shared Prisma client. Imported everywhere we need DB access.
# We don't create it here — it's created once in prisma.py and reused.

from .routes import auth, comments, posts, users
# Our three route modules. Each exposes a `router` (an APIRouter).
#   auth     → /auth/register, /auth/login, /auth/me
#   posts    → /posts/... CRUD
#   comments → /posts/{id}/comments, /comments/{id}


# ---------------------------------------------------------------------------
# LIFESPAN — startup & shutdown hooks
# ---------------------------------------------------------------------------
# Before this runs, nothing can touch the DB.
# After this yields, the server is accepting requests.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    if not prisma.is_connected():
        await prisma.connect()  # open the pool / engine connection
    print("[Database] Connected successfully")

    yield  # <-- server runs while we're paused here

    # ---- Shutdown ----
    if prisma.is_connected():
        await prisma.disconnect()  # close cleanly (important for tests)
    print("[Database] Disconnected successfully")


# ---------------------------------------------------------------------------
# APP INSTANCE
# ---------------------------------------------------------------------------
# title → shown in /docs (Swagger UI).
# lifespan → wires in the startup/shutdown hooks above.
app = FastAPI(
    lifespan=lifespan,
    title="Noo Blog API",
)


# ---------------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------------
# Every router is mounted under /api/v1 so we can version the API later
# (e.g. add /api/v2 without touching v1 clients).
app.include_router(auth.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(users.router,    prefix="/api/v1")

# ---------------------------------------------------------------------------
# ROOT ROUTE — sanity check
# ---------------------------------------------------------------------------
# Hit http://localhost:8000/ to confirm the server is alive.
@app.get("/")
async def root():
    return {"message": "Noo Blog API 🚀"}
