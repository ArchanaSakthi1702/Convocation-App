from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List,Optional
from sqlalchemy.orm import joinedload


from app.database import get_db
from app.models import User,Class
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
    # Eager load relationships with joinedload to avoid lazy load in async
    query = select(User).options(
        joinedload(User.assigned_classes).joinedload(Class.program_type_ref),
        joinedload(User.assigned_classes).joinedload(Class.class_name_ref)
    )

    result = await db.execute(query)
    staff_list = result.scalars().unique().all()  # remove duplicates if any

    filtered_staff = []
    for staff in staff_list:
        # Safe role check
        staff_role = getattr(staff.role, "value", staff.role)
        if role and staff_role != role:
            continue

        # Safe gender check
        if gender and staff.gender != gender:
            continue

        # Program type filter
        if program_type:
            if not staff.assigned_classes or not any(
                getattr(c.program_type_ref, "type_name", None) == program_type
                for c in staff.assigned_classes
            ):
                continue

        filtered_staff.append(
            StaffRead(
                id=str(staff.id),
                staff_name=staff.staff_name,
                staff_roll_number=staff.staff_roll_number,
                role=staff_role,
                gender=staff.gender,
                assigned_classes=[
                    c.class_name_ref.name for c in staff.assigned_classes if c.class_name_ref
                ] if staff.assigned_classes else []
            )
        )

    return {"count": len(filtered_staff), "staffs": filtered_staff}

