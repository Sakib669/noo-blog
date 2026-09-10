from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional
from ..dependencies import require_auth
from ..prisma import prisma
from prisma.models import User
from prisma.errors import PrismaError
import re

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
    author: dict  # we'll include a simplified author object


# Helper: convert Prisma post dict to response
def post_to_response(post, include_author=True):
    result = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "summary": post.summary,
        "cover_image": post.cover_image,
        "published": post.published,
        "views": post.views,
        "tags": post.tags,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }
    if include_author and hasattr(post, "author"):
        result["author"] = {
            "id": post.author.id,
            "username": post.author.username,
            "full_name": post.author.full_name,
            "avatar": post.author.avatar,
        }
    return result


def generate_slug(title: str) -> str:
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
    # Remove multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


# ---------- Endpoints ----------


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(post_data: PostCreate, user: User = Depends(require_auth)):
    # Generate slug from title
    slug = generate_slug(post_data.title)
    # Ensure slug uniqueness
    existing = await prisma.post.find_unique(where={"slug": slug})
    if existing:
        # Append a random suffix
        import uuid

        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    try:
        new_post = await prisma.post.create(
            data={
                "title": post_data.title,
                "slug": slug,
                "content": post_data.content,
                "summary": post_data.summary,
                "cover_image": post_data.cover_image,
                "tags": post_data.tags,
                "author": {"connect": {"id": user.id}},
            },
            include={"author": True},
        )
        return post_to_response(new_post)
    except PrismaError as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


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
    return [post_to_response(p) for p in posts]


@router.get("/{slug}", response_model=PostResponse)
async def get_post_by_slug(slug: str):
    post = await prisma.post.find_unique(where={"slug": slug}, include={"author": True})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    # Increment view count
    await prisma.post.update(where={"id": post.id}, data={"views": {"increment": 1}})
    # Return updated post (we can re-fetch or update the view count in response)
    post.views += 1
    return post_to_response(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str, post_data: PostUpdate, user: User = Depends(require_auth)
):
    # Check if post exists
    post = await prisma.post.find_unique(
        where={"id": post_id}, include={"author": True}
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Authorization: only author or admin (add role check later)
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")

    # Prepare update data
    update_dict = post_data.dict(exclude_unset=True)
    if "title" in update_dict:
        # Regenerate slug if title changes
        new_slug = generate_slug(update_dict["title"])
        # Ensure uniqueness
        existing = await prisma.post.find_first(
            where={"slug": new_slug, "id": {"not": post_id}}
        )
        if existing:
            import uuid

            new_slug = f"{new_slug}-{str(uuid.uuid4())[:8]}"
        update_dict["slug"] = new_slug

    try:
        updated = await prisma.post.update(
            where={"id": post_id}, data=update_dict, include={"author": True}
        )
        return post_to_response(updated)
    except PrismaError as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, user: User = Depends(require_auth)):
    post = await prisma.post.find_unique(where={"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    await prisma.post.delete(where={"id": post_id})
    return None  # 204 No Content


@router.patch("/{post_id}/publish", response_model=PostResponse)
async def toggle_publish(post_id: str, user: User = Depends(require_auth)):
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
    return post_to_response(updated)
