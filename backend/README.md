# Noo Blog API — Backend

FastAPI + Prisma (PostgreSQL) backend with JWT authentication, full post lifecycle management, comments, and AI-powered post summarization using Google Gemini.

---

## Project Structure

```text
backend/
├── prisma/
│   ├── migrations/
│   └── schema.prisma        # Database models (User, Post, Comment)
├── src/
│   └── app/
│       ├── main.py          # FastAPI app & lifespan configuration
│       ├── config.py        # Environment settings & .env loading
│       ├── dependencies.py  # Auth dependencies (get_current_user)
│       ├── models.py        # Pydantic request/response schemas
│       ├── prisma.py        # Prisma client instance
│       ├── routes/
│       │   ├── auth.py      # /api/v1/auth (register, login, me)
│       │   ├── users.py     # /api/v1/users (profile, password, public view)
│       │   ├── posts.py     # /api/v1/posts (CRUD, publish, AI summarize)
│       │   └── comments.py  # /api/v1/posts/{id}/comments & /api/v1/comments/{id}
│       ├── services/
│       │   └── ai_service.py # Gemini LLM integration
│       └── utils/
│           └── security.py  # bcrypt hashing & JWT tokens
├── .env                     # Database URL, JWT secrets, Gemini API key
├── pyproject.toml           # uv project configuration
└── test_all_endpoints.py    # Automated test suite (31 checks)
```

---

## Getting Started

### 1. Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- PostgreSQL running on `localhost:5432` with database `noo_blog`

### 2. Install & Generate Prisma Client
Inside the `backend` directory:
```powershell
uv sync
uv run prisma generate
```

### 3. Run the Development Server
```powershell
uv run uvicorn src.app.main:app --reload --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 4. Run Endpoint Verification Suite
```powershell
uv run python test_all_endpoints.py
```
