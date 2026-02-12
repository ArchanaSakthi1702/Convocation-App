from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional,List

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Class, UserRole
from app.schemas.listing_for_attendance import AttendanceStaffResponse,ClassInfoWithStudents,StudentInfo



router = APIRouter(prefix="/attendance-staff", tags=["Attendance Incharge Attendance Listing"])

@router.get("/list-students", response_model=AttendanceStaffResponse)
async def list_students_for_attendance_incharge(
    present: Optional[bool] = Query(
        None,
        description="Filter by attendance status: true=present, false=absent"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # 🔹 Load full user with roles + classes + students
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.roles),  # ✅ load roles
            selectinload(User.assigned_classes)
            .selectinload(Class.students),
            selectinload(User.assigned_classes)
            .selectinload(Class.class_name_ref)
        )
        .where(User.id == current_user.id)
    )

    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔹 Proper role check (many-to-many)
    has_attendance_role = any(
        role.name == UserRole.attendance_incharge
        for role in staff.roles
    )

    if not has_attendance_role:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not staff.assigned_classes:
        return AttendanceStaffResponse(
            staff_id=str(staff.id),
            staff_name=staff.staff_name or "",
            staff_gender=staff.gender,
            assigned_classes_count=0,
            classes=[]
        )

    response_data: List[ClassInfoWithStudents] = []

    for c in staff.assigned_classes:

        # 🔹 Gender filtering logic
        if staff.can_handle_both_genders:
            students_filtered_by_gender = c.students
        else:
            students_filtered_by_gender = [
                s for s in c.students if s.gender == staff.gender
            ]

        # 🔹 Apply attendance filter
        if present is not None:
            students_filtered_by_gender = [
                s for s in students_filtered_by_gender
                if s.present == present
            ]

        filtered_students = [
            StudentInfo(
                student_id=str(s.id),
                roll_number=s.roll_number,
                name=s.name,
                gender=s.gender,
                present=s.present
            )
            for s in students_filtered_by_gender
        ]

        response_data.append(
            ClassInfoWithStudents(
                class_id=str(c.id),
                class_name=c.class_name_ref.name if c.class_name_ref else None,
                department=c.department,
                section=c.section,
                regular_or_self=c.regular_or_self,
                students_count=len(filtered_students),
                students=filtered_students
            )
        )

    return AttendanceStaffResponse(
        staff_id=str(staff.id),
        staff_name=staff.staff_name or "",
        staff_gender=staff.gender,
        assigned_classes_count=len(staff.assigned_classes),
        classes=response_data
    )
