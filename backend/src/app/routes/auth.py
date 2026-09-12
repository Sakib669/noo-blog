from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models import TokenResponse, UserLogin, UserRegister, UserResponse
from ..prisma import prisma
from ..utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _to_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        avatar=user.avatar,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(payload: UserRegister):
    existing = await prisma.user.find_first(
        where={"OR": [{"email": payload.email}, {"username": payload.username}]}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already taken")

    new_user = await prisma.user.create(
        data={
            "email": payload.email,
            "username": payload.username,
            "password": hash_password(payload.password),
            "full_name": payload.full_name,
        }
    )
    return _to_response(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user = await prisma.user.find_unique(where={"email": payload.email})
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=_to_response(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):  # noqa: B008
    return _to_response(current_user)