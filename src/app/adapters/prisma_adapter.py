from typing import Optional, Dict, Any, List
from fastauth.adapters.base import DatabaseAdapter
from prisma import Client
from prisma.models import User as PrismaUser
from datetime import datetime


class PrismaAdapter(DatabaseAdapter):
    """
    FastAuth database adapter using Prisma.
    """

    def __init__(self, client: Client):
        self.client = client

    # ---------- User methods ----------

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        # user_data will contain: email, password (hashed by FastAuth), and any extra fields
        # We need to map to our Prisma User model.
        # We assume the model has: email, password, username, full_name, etc.
        # If username not provided, we can use email as username or generate one.
        # For simplicity, we'll require username in the sign-up form.
        # FastAuth allows extra fields via the 'metadata' field, but we can directly accept them.
        # We'll expect 'username' and 'full_name' in user_data.
        user_data = user_data.copy()
        # Remove any fields not in our Prisma model to avoid errors
        allowed_fields = {"email", "password", "username", "full_name", "bio", "avatar"}
        filtered = {k: v for k, v in user_data.items() if k in allowed_fields}
        # Ensure required fields are present
        if "username" not in filtered:
            # Generate username from email
            filtered["username"] = filtered["email"].split("@")[0]
        if "full_name" not in filtered:
            filtered["full_name"] = filtered["username"]
        # Create user in database
        new_user = await self.client.user.create(data=filtered)
        return self._user_to_dict(new_user)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user = await self.client.user.find_unique(where={"email": email})
        return self._user_to_dict(user) if user else None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = await self.client.user.find_unique(where={"id": user_id})
        return self._user_to_dict(user) if user else None

    async def update_user(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        # Filter allowed fields
        allowed = {"email", "username", "full_name", "bio", "avatar", "password"}
        filtered = {k: v for k, v in update_data.items() if k in allowed}
        if not filtered:
            return await self.get_user_by_id(user_id)
        updated = await self.client.user.update(where={"id": user_id}, data=filtered)
        return self._user_to_dict(updated)

    async def delete_user(self, user_id: str) -> None:
        await self.client.user.delete(where={"id": user_id})

    # ---------- Session methods (if using sessions) ----------
    # FastAuth can work with JWT only, so we may not need session storage.
    # If you plan to use database sessions, implement these.
    # For JWT-only, we can leave them as stubs.
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Not used for JWT strategy
        return session_data

    async def get_session_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        return None

    async def delete_session(self, token: str) -> None:
        pass

    # ---------- Helper ----------
    def _user_to_dict(self, user: PrismaUser) -> Dict[str, Any]:
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.bio,
            "avatar": user.avatar,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
