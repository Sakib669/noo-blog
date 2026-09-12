# ---------------------------------------------------------------------------
# Comments API — comments nested under posts
# ---------------------------------------------------------------------------
# Endpoints implemented in this file:
#   POST   /api/v1/posts/{post_id}/comments   → add a comment (auth required)
#   GET    /api/v1/posts/{post_id}/comments   → list comments (public)
#   DELETE /api/v1/comments/{comment_id}      → delete own comment (auth)
#
# Design notes:
#   • This router has NO prefix because the two URL families live at
#     different roots: one nests under /posts/{id}, the other stands alone.
#     We therefore write the full path on each decorator.
# ---------------------------------------------------------------------------

from typing import List, Optional
# List    → lets us annotate "a list of CommentResponse" for FastAPI's docs.
# Optional→ marks a field as "may be None" (like TypeScript's T | null).

from fastapi import APIRouter, Depends, HTTPException, Query, status
# APIRouter     → groups related routes; we mount this in main.py
# Depends       → dependency injection (like NestJS @Injectable plumbing)
# HTTPException → raise HTTP errors (equivalent to Nest's HttpException)
# Query         → declares + validates query parameters (?skip=0&limit=20)
# status        → named constants, e.g. status.HTTP_201_CREATED (201)

from pydantic import BaseModel, Field
# BaseModel → base class for our request/response schemas (like Zod objects)
# Field     → per-field validation, e.g. min_length, max_length

from ..dependencies import get_current_user
# Our JWT dependency. Reads the Authorization: Bearer header,
# validates the token, and returns the Prisma User row — or raises 401.

from ..prisma import prisma
# The single Prisma client instance that we connected to in main.py's lifespan.


# ---------------------------------------------------------------------------
# 1. ROUTER
# ---------------------------------------------------------------------------
router = APIRouter(tags=["comments"])
# tags=["comments"] → groups these endpoints under "comments" in /docs.


# ---------------------------------------------------------------------------
# 2. PYDANTIC SCHEMAS
# ---------------------------------------------------------------------------


class CommentCreate(BaseModel):
    """Request body for creating a comment."""

    content: str = Field(..., min_length=1, max_length=1000)
    # "..." means "required" (no default).
    # min_length=1   → reject empty strings.
    # max_length=1000→ cheap guard against abuse / DOS via giant payloads.


class CommentResponse(BaseModel):
    """Shape of a comment we return to the client."""

    id: str
    content: str
    created_at: str  # ISO 8601 string, e.g. "2026-09-12T10:30:00"
    post_id: str
    author: Optional[dict] = None
    # We attach a small author summary (id, username, full_name, avatar).
    # We do NOT send the full user object — never leak the password hash.


# ---------------------------------------------------------------------------
# 3. HELPER — Prisma model → response schema
# ---------------------------------------------------------------------------


def _to_response(comment, include_author: bool = True) -> CommentResponse:
    """
    Convert a Prisma Comment instance into a CommentResponse.

    Why: Prisma returns rich model objects (with nested `.author` if we asked
    for it). Pydantic can't serialize those, so we flatten them here.
    """
    author = None
    # getattr(obj, name, default) safely reads an attribute that may not
    # exist (e.g. if we queried without include={"author": True}).
    if include_author and getattr(comment, "author", None):
        author = {
            "id": comment.author.id,
            "username": comment.author.username,
            "full_name": comment.author.full_name,
            "avatar": comment.author.avatar,
        }

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at.isoformat(),  # datetime → string
        post_id=comment.post_id,
        author=author,
    )


# ---------------------------------------------------------------------------
# 4. ENDPOINTS
# ---------------------------------------------------------------------------


@router.post(
    "/posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,  # 201, not the default 200
    response_model=CommentResponse,  # documents + filters the response
)
async def create_comment(
    post_id: str,  # taken from the URL path
    payload: CommentCreate,  # request body, validated by Pydantic
    user=Depends(get_current_user),  # noqa: B008 → silences Ruff
):
    """Add a comment to a post. Requires authentication."""
    # (a) Verify the target post exists. Prisma would reject the insert
    # anyway (foreign key), but a friendly 404 beats a raw DB error.
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # (b) Insert the comment. We use Prisma's "connect" syntax to link
    # both relations atomically — no manual author_id / post_id juggling.
    new_comment = await prisma.comment.create(
        data={
            "content": payload.content,
            "author": {"connect": {"id": user.id}},  # the logged-in user
            "post": {"connect": {"id": post_id}},  # the post we just checked
        },
        # include={"author": True} → Prisma returns the author row too,
        # saving us a second query.
        include={"author": True},
    )

    # (c) Shape and return.
    return _to_response(new_comment)


@router.get(
    "/posts/{post_id}/comments",
    response_model=List[CommentResponse],  # a LIST of CommentResponse
)
async def list_comments(
    post_id: str,
    skip: int = Query(0, ge=0),  # offset, must be >= 0
    limit: int = Query(20, ge=1, le=100),  # page size, between 1 and 100
):
    """Return comments for a post, oldest first. Public endpoint."""
    # (a) Same 404 guard so a typo in post_id returns 404 instead of [].
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # (b) Fetch. Order asc (oldest first) — matches typical thread UX.
    comments = await prisma.comment.find_many(
        where={"post_id": post_id},
        skip=skip,
        take=limit,
        include={"author": True},
        order={"created_at": "asc"},
    )

    # (c) List comprehension: same as
    #     result = []
    #     for c in comments: result.append(_to_response(c))
    return [_to_response(c) for c in comments]


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,  # 204 = success, no body
)
async def delete_comment(
    comment_id: str,
    user=Depends(get_current_user),  # noqa: B008
):
    """Delete a comment. Only the original author may do so."""
    # (a) Fetch first — we need author_id to enforce ownership.
    comment = await prisma.comment.find_unique(where={"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # (b) Authorization check. 403 (forbidden) ≠ 401 (unauthenticated):
    #     401 = "you're not logged in"
    #     403 = "you are, but this isn't yours"
    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # (c) Delete.
    await prisma.comment.delete(where={"id": comment_id})

    # (d) Return None. FastAPI turns this into an empty 204 response body.
    return None
