from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import require_auth
from prisma.models import User
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreate(BaseModel):
    title: str
    content: str


@router.post("/")
async def create_post(post_data: PostCreate, user: User = Depends(require_auth)):
    # user is the authenticated user object from Prisma
    # Now you can create a post associated with this user
    # (you'll need to import the prisma client and use it)
    from ..prisma import prisma

    new_post = await prisma.post.create(
        data={
            "title": post_data.title,
            "slug": post_data.title.lower().replace(" ", "-"),
            "content": post_data.content,
            "author": {"connect": {"id": user.id}},
        }
    )
    return {"message": "Post created", "post": new_post}


@router.get("/")
async def list_posts():
    from ..prisma import prisma

    posts = await prisma.post.find_many(
        where={"published": True},
        include={"author": True},
        order={"created_at": "desc"},
    )
    return posts
