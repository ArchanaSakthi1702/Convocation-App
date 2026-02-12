from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload

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
    # Load user with roles
    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(func.lower(User.staff_roll_number) == staff_roll_number.lower())
    )

    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid roll number")

    # Extract role names
    role_names = [role.name for role in user.roles]

    # Allow only attendance or certificate staff
    allowed_roles = {
        UserRole.attendance_incharge,
        UserRole.certificate_incharge,
        UserRole.hod
    }

    if not any(role in allowed_roles for role in role_names):
        raise HTTPException(status_code=403, detail="Not a staff user")

    # Token data
    token_data = {
        "user_id": str(user.id),
        "roles": [role.value for role in role_names],  # ✅ list of roles
        "gender": user.gender,
        "can_handle_both_genders": user.can_handle_both_genders
    }

    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "roles": [role.value for role in role_names],
        "can_handle_both_genders": user.can_handle_both_genders
    }
