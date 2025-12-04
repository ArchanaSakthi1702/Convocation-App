from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, UserRole
from app.auth.jwt import decode_access_token
import uuid

bearer_scheme = HTTPBearer()




# ------------------ Helper ------------------ #
async def get_user_by_id(user_id: bytes, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ------------------ Current user ------------------ #
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        else:
            user_id = user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(user_id, db)
    return user


# ---------------- Role-based dependencies ---------------- #

async def is_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def is_staff_of_this_class(class_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.attendance_incharge:
        raise HTTPException(status_code=403, detail="Attendance staff access required")
    class_id_bytes = uuid.UUID(class_id)
    # Check if staff has this class assigned
    if not any(c.id == class_id_bytes for c in current_user.assigned_classes):
        raise HTTPException(status_code=403, detail="Not assigned to this class")
    return current_user


async def is_certificate_staff_of_this_class(class_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.certificate_incharge:
        raise HTTPException(status_code=403, detail="Certificate staff access required")
    class_id_bytes = uuid.UUID(class_id)
    if not any(c.id == class_id_bytes for c in current_user.assigned_classes):
        raise HTTPException(status_code=403, detail="Not assigned to this class")
    return current_user
