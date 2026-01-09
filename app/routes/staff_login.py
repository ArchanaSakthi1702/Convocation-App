from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from datetime import timedelta
import uuid

from app.database import get_db
from app.models import User, UserRole
from app.routes import SPECIAL_BOTH_ROLE_IDS
from app.auth.jwt import create_access_token

router = APIRouter(
    prefix="/staff"
)



@router.post("/login")
async def staff_login(
    staff_roll_number: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(
        func.lower(User.staff_roll_number) == staff_roll_number.lower()
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid roll number")

    # Allow only staff roles
    if user.role not in [
        UserRole.attendance_incharge,
        UserRole.certificate_incharge
    ]:
        raise HTTPException(status_code=403, detail="Not a staff user")

    # ✅ Special access logic
    can_access_both = user.staff_roll_number in SPECIAL_BOTH_ROLE_IDS

    token_data = {
        "user_id": str(user.id),
        "role": user.role.value,        # always actual DB role
        "gender": user.gender,
        "can_access_both": can_access_both
    }

    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "can_access_both":can_access_both
    }