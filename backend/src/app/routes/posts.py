import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional

from ..dependencies import get_current_user
from ..prisma import prisma
from ..services.ai_service import SummarizationError, summarize_text

router = APIRouter(prefix="/posts", tags=["posts"])


# ---------- Pydantic Schemas ----------
class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10)
    summary: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=500)
    tags: List[str] = []


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    summary: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    published: Optional[bool] = None


class PostResponse(BaseModel):
    id: str
    title: str
    slug: str
    content: str
    summary: Optional[str]
    cover_image: Optional[str]
    published: bool
    views: int
    tags: List[str]
    created_at: str
    updated_at: str
    author: Optional[dict] = None


# ---------- Helpers ----------
def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
    return re.sub(r"-+", "-", slug)


def _to_response(post, include_author: bool = True) -> PostResponse:
    author = None
    if include_author and getattr(post, "author", None):
        author = {
            "id": post.author.id,
            "username": post.author.username,
            "full_name": post.author.full_name,
            "avatar": post.author.avatar,
        }
    return PostResponse(
        id=post.id,
        title=post.title,
        slug=post.slug,
        content=post.content,
        summary=post.summary,
        cover_image=post.cover_image,
        published=post.published,
        views=post.views,
        tags=post.tags,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
        author=author,
    )


# ---------- Endpoints ----------
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(payload: PostCreate, user=Depends(get_current_user)):  # noqa: B008
    slug = _slugify(payload.title)
    existing = await prisma.post.find_unique(where={"slug": slug})
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"

    new_post = await prisma.post.create(
        data={
            "title": payload.title,
            "slug": slug,
            "content": payload.content,
            "summary": payload.summary,
            "cover_image": payload.cover_image,
            "tags": payload.tags,
            "author": {"connect": {"id": user.id}},
        },
        include={"author": True},
    )
    return _to_response(new_post)


@router.get("/", response_model=List[PostResponse])
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    tag: Optional[str] = None,
    search: Optional[str] = None,
):
    where = {"published": True}
    if tag:
        where["tags"] = {"has": tag}
    if search:
        where["OR"] = [
            {"title": {"contains": search, "mode": "insensitive"}},
            {"content": {"contains": search, "mode": "insensitive"}},
        ]

    posts = await prisma.post.find_many(
        where=where,
        skip=skip,
        take=limit,
        include={"author": True},
        order={"created_at": "desc"},
    )
    return [_to_response(p) for p in posts]


@router.get("/{slug}", response_model=PostResponse)
async def get_post(slug: str):
    post = await prisma.post.find_unique(where={"slug": slug}, include={"author": True})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await prisma.post.update(
        where={"id": post.id},
        data={"views": {"increment": 1}},
    )
    post.views += 1
    return _to_response(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    payload: PostUpdate,
    user=Depends(get_current_user),  # noqa: B008
):
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    data = payload.model_dump(exclude_unset=True)

    if "title" in data:
        new_slug = _slugify(data["title"])
        clash = await prisma.post.find_first(
            where={"slug": new_slug, "id": {"not": post_id}}
        )
        if clash:
            new_slug = f"{new_slug}-{uuid.uuid4().hex[:8]}"
        data["slug"] = new_slug

    updated = await prisma.post.update(
        where={"id": post_id}, data=data, include={"author": True}
    )
    return _to_response(updated)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, user=Depends(get_current_user)):  # noqa: B008
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await prisma.post.delete(where={"id": post_id})
    return None


@router.patch("/{post_id}/publish", response_model=PostResponse)
async def toggle_publish(post_id: str, user=Depends(get_current_user)):  # noqa: B008
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated = await prisma.post.update(
        where={"id": post_id},
        data={"published": not post.published},
        include={"author": True},
    )
    return _to_response(updated)


@router.post("/{post_id}/summarize", response_model=PostResponse)
async def summarize_post(
    post_id: str,
    force: bool = False,
    user=Depends(get_current_user),  # noqa: B008
):
    """Generate an AI summary for a post and save it to the DB.

    - Only the author may trigger this.
    - If a summary already exists, it is returned as-is — unless
      `?force=true` is passed, which regenerates it.

    The expensive LLM call happens inline; for a first version this is
    fine. If you later expect heavy traffic, move it to a background
    worker (Celery / RQ / FastAPI BackgroundTasks) and return 202.
    """
    # (a) Fetch the post — we need its content and its author.
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # (b) Authorization: only the author can summarize their own post.
    #     This avoids strangers burning your LLM quota on someone else's
    #     content.
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # (c) If a summary already exists and force isn't set, return cached.
    #     `force` is a query param → /posts/{id}/summarize?force=true
    if post.summary and not force:
        # Re-fetch with author included so the response matches PostResponse.
        post_with_author = await prisma.post.find_unique(
            where={"id": post_id},
            include={"author": True},
        )
        return _to_response(post_with_author)

    # (d) Guard: can't summarize a post with no content.
    if not post.content or not post.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Post has no content to summarize",
        )

    # (e) Call the AI service. This is the slow part (1–5 s).
    try:
        summary = await summarize_text(post.content)
    except SummarizationError as exc:
        # 502 Bad Gateway = "our upstream (the LLM) failed".
        # This is more accurate than 500 — the problem isn't our server.
        raise HTTPException(status_code=502, detail=str(exc))

    # (f) Persist the summary on the post row, then re-fetch with author
    #     included so the response includes the author block.
    updated = await prisma.post.update(
        where={"id": post_id},
        data={"summary": summary},
        include={"author": True},
    )
    return _to_response(updated)
