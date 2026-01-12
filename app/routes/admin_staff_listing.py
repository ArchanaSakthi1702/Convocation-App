from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,or_
from typing import List,Optional
from sqlalchemy.orm import joinedload

import enum
from app.database import get_db
from app.models import User,Class,ProgramType
from app.auth.dependencies import is_admin
from app.schemas.staff_schemas import StaffRead,StaffListResponse,StaffRead2,AssignedClassRead

router=APIRouter(
    prefix="/admin",
    tags=["Admin Staffs Listing"]
)



@router.get("/staff/search", dependencies=[Depends(is_admin)])
async def search_staff(
    q: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Search staff by name or roll number (with assigned class IDs & names)
    """

    query = (
        select(User)
        .options(
            joinedload(User.assigned_classes)
            .joinedload(Class.class_name_ref)
        )
        .where(
            or_(
                User.staff_name.ilike(f"%{q}%"),
                User.staff_roll_number.ilike(f"%{q}%")
            )
        )
    )

    result = await db.execute(query)
    staffs = result.scalars().unique().all()

    return {
        "count": len(staffs),
        "results": [
            {
                "staff_id": str(staff.id),
                "staff_name": staff.staff_name,
                "staff_roll_number": staff.staff_roll_number,
                "role": staff.role.value if isinstance(staff.role, enum.Enum) else staff.role,
                "gender": staff.gender,
                "assigned_classes": [
                    {
                        "id": str(c.id),
                        "name": c.class_name_ref.name
                    }
                    for c in staff.assigned_classes
                    if c.class_name_ref
                ]
            }
            for staff in staffs
        ]
    }

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

@router.get(
    "/list-staffs-with-assighned_classes",
    dependencies=[Depends(is_admin)]
)
async def list_all_staff2(
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

    # Filters
    if role:
        query = query.where(User.role == role)

    if gender:
        query = query.where(User.gender == gender)

    if program_type:
        query = (
            query
            .join(User.assigned_classes)
            .join(Class.program_type_ref)
            .where(ProgramType.type_name == program_type)
        )

    result = await db.execute(query)
    staff_list = result.scalars().unique().all()

    filtered_staff = []

    for staff in staff_list:
        # Fallbacks for None
        name = staff.staff_name or ""
        roll = staff.staff_roll_number or ""
        gender_val = staff.gender or ""
        role_val = staff.role.value if isinstance(staff.role, enum.Enum) else staff.role

        # Assigned classes
        assigned_classes = [
            AssignedClassRead(
                id=str(c.id),
                name=c.class_name_ref.name if c.class_name_ref else ""
            )
            for c in staff.assigned_classes or []
        ]

        filtered_staff.append(
            StaffRead2(
                id=str(staff.id),
                staff_name=name,
                staff_roll_number=roll,
                role=role_val,
                gender=gender_val,
                assigned_classes=assigned_classes
            )
        )

    # Return as dict without wrapping in another Pydantic model
    return {
        "count": len(filtered_staff),
        "staffs": filtered_staff
    }
