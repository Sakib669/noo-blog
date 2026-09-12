# ---------------------------------------------------------------------------
# Users API — public profiles and self-service profile management
# ---------------------------------------------------------------------------
# Endpoints:
#   GET  /api/v1/users/{username}          → public profile (no auth)
#   GET  /api/v1/users/{username}/posts    → that user's published posts
#   PUT  /api/v1/users/me                  → update own profile   (auth)
#   PUT  /api/v1/users/me/password         → change own password (auth)
#
# Ordering note: the `/me` routes MUST be declared BEFORE the `/{username}`
# route. FastAPI matches routes in declaration order, so if `/{username}`
# came first, the literal path "me" would be captured as a username.
# ---------------------------------------------------------------------------

from typing import List, Optional
# List, Optional — type hints for the response models below.

from fastapi import APIRouter, Depends, HTTPException, status
# Same imports as posts.py and comments.py; see those files for details.

from pydantic import BaseModel
# (Not used directly here — we import our schemas from ..models.)

from ..dependencies import get_current_user
# JWT dependency → returns the authenticated Prisma User or raises 401.

from ..models import (
    PasswordChange,
    PublicUserResponse,
    UserUpdate,
)
# Import only what we need. Notice we don't import UserResponse — the
# public profile uses PublicUserResponse (no email).

from ..prisma import prisma
# Shared Prisma client.

from ..utils.security import hash_password, verify_password
# Password utilities. `verify_password` is what lets us check the current
# password before allowing a change.


# ---------------------------------------------------------------------------
# 1. ROUTER
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/users", tags=["users"])
# All routes below start with /users, so we declare the prefix once here.


# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------

def _to_public(user) -> PublicUserResponse:
    """Convert a Prisma User row into a PublicUserResponse.

    We strip email and password here — this function is the single
    chokepoint that decides what "public" means. Change it once, and
    every public endpoint is updated consistently.
    """
    return PublicUserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        avatar=user.avatar,
        created_at=user.created_at.isoformat(),
    )


def _to_post_summary(post) -> dict:
    """Trim a Post row down to just the fields a listing needs.

    We could return the full PostResponse from posts.py, but author
    pages are read-heavy: keeping the payload small matters.
    """
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "summary": post.summary,
        "cover_image": post.cover_image,
        "tags": post.tags,
        "views": post.views,
        "created_at": post.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# 3. SELF-SERVICE ENDPOINTS  (declared first — see ordering note above)
# ---------------------------------------------------------------------------

@router.put("/me", response_model=PublicUserResponse)
async def update_me(
    payload: UserUpdate,
    user=Depends(get_current_user),          # noqa: B008
):
    """Update the currently logged-in user's profile.

    Only fields present in the request body are updated. Omitted fields
    are left untouched (partial update semantics).
    """
    # model_dump(exclude_unset=True) → a dict containing ONLY the fields
    # the client actually sent. If they sent {"bio": "hi"}, we get
    # {"bio": "hi"} and nothing else. Without exclude_unset, every field
    # would appear with value None and we'd wipe existing data.
    update_data = payload.model_dump(exclude_unset=True)

    # No fields sent → nothing to do. Return the current state (200).
    if not update_data:
        return _to_public(user)

    # `exclude_unset=True` already dropped untouched fields, but a client
    # could still send `"bio": null` explicitly to clear the bio. That's
    # fine: None is a valid value for a nullable column.
    updated = await prisma.user.update(
        where={"id": user.id},
        data=update_data,
    )
    return _to_public(updated)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChange,
    user=Depends(get_current_user),          # noqa: B008
):
    """Change the logged-in user's password.

    Requires the current password as proof of identity — this protects
    against session-hijack scenarios where an attacker has a stolen token
    but not the original password.
    """
    # (a) Verify the *current* password matches what's on file.
    #     If not, return 400 (bad request) rather than 401, because the
    #     user IS authenticated — it's the payload that's wrong.
    if not verify_password(payload.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # (b) Optional sanity check: reject no-op changes so the user gets
    #     clear feedback instead of a silent "success".
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must differ from current password",
        )

    # (c) Hash the new password with bcrypt and persist it.
    #     Never store plaintext. Never log it.
    await prisma.user.update(
        where={"id": user.id},
        data={"password": hash_password(payload.new_password)},
    )

    # 204 No Content → nothing to return. Client just sees success.
    return None


# ---------------------------------------------------------------------------
# 4. PUBLIC ENDPOINTS
# ---------------------------------------------------------------------------

@router.get("/{username}", response_model=PublicUserResponse)
async def get_user_profile(username: str):
    """Return a user's public profile by username.

    Username is used (not id) because it's the human-friendly, URL-safe
    identifier we want in links like /users/sakib.
    """
    user = await prisma.user.find_unique(where={"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_public(user)


@router.get("/{username}/posts", response_model=List[dict])
async def get_user_posts(
    username: str,
    skip:  int = 0,
    limit: int = 10,
):
    """List a user's PUBLISHED posts, newest first. Public endpoint.

    Drafts are intentionally hidden: they belong to the author alone.
    """
    # (a) Resolve the username → id. Returning 404 here gives a clear
    #     error rather than an empty list for a typo'd username.
    user = await prisma.user.find_unique(where={"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # (b) Fetch. Note the compound where clause:
    #     { author_id: <id>, published: True }
    #     Prisma translates this into a single SQL WHERE with two conditions.
    posts = await prisma.post.find_many(
        where={"author_id": user.id, "published": True},
        skip=skip,
        take=limit,
        order={"created_at": "desc"},
    )

    # (c) Trim to summary fields for a compact list payload.
    return [_to_post_summary(p) for p in posts]