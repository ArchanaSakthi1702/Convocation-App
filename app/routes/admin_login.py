from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timedelta
import uuid

from app.database import get_db
from app.models import User, UserRole
from app.auth.security import verify_password
from app.auth.jwt import create_access_token

router = APIRouter(
    prefix="/admin"
)
@router.post("/login")
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin login using username + password.
    Returns JWT token with user_id and role.
    """

    # Fetch user with roles eagerly loaded
    stmt = select(User).where(User.username == form_data.username).options(selectinload(User.roles))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Verify password
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # ✅ Check if user has admin role
    role_names = [role.name for role in user.roles]

    if "admin" not in role_names:
        raise HTTPException(status_code=403, detail="Not an admin user")

    # Prepare token data
    token_data = {
        "user_id": str(user.id),
        "roles": role_names   # better to send list
    }

    # Create JWT access token
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}
