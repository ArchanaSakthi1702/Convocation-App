from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import uuid

from app.database import get_db
from app.models import User, UserRole
from app.auth.jwt import create_access_token

router = APIRouter(
    prefix="/staff"
)



@router.post("/login")
async def staff_login(
    staff_roll_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Staff login using their roll number.
    Returns JWT token with user_id, role, and gender.
    """
    stmt = select(User).where(User.staff_roll_number == staff_roll_number)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid roll number")

    if user.role not in [UserRole.attendance_incharge, UserRole.certificate_incharge]:
        raise HTTPException(status_code=403, detail="Not a staff user")

    token_data = {
        "user_id": str(user.id), 
        "role": user.role,
        "gender": user.gender  # store gender in token
    }

    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}
