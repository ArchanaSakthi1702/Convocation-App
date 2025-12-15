from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List,Optional
from sqlalchemy.orm import joinedload

import enum
from app.database import get_db
from app.models import User,Class,ProgramType
from app.auth.dependencies import is_admin
from app.schemas.staff_schemas import StaffRead,StaffListResponse

router=APIRouter(
    prefix="/admin",
    tags=["Admin Staffs Listing"]
)


@router.get("/list-staffs", response_model=StaffListResponse, dependencies=[Depends(is_admin)])
async def list_all_staff(
    role: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    program_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).options(
        joinedload(User.assigned_classes)
        .joinedload(Class.program_type_ref),
        joinedload(User.assigned_classes)
        .joinedload(Class.class_name_ref)
    )

    # Apply filters at DB level
    if role:
        query = query.where(User.role == role)
    if gender:
        query = query.where(User.gender == gender)
    if program_type:
        query = query.join(User.assigned_classes).join(Class.program_type_ref).where(
            ProgramType.type_name == program_type
        )

    result = await db.execute(query)
    staff_list = result.scalars().unique().all()  # remove duplicates

    filtered_staff = []

    for staff in staff_list:
        filtered_staff.append(
            StaffRead(
                id=str(staff.id),
                staff_name=staff.staff_name,
                staff_roll_number=staff.staff_roll_number,
                role=staff.role.value if isinstance(staff.role, enum.Enum) else staff.role,
                gender=staff.gender,
                assigned_classes=[c.class_name_ref.name for c in staff.assigned_classes if c.class_name_ref]
            )
        )

    return {"count": len(filtered_staff), "staffs": filtered_staff}