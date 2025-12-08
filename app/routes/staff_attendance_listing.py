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
    present: Optional[bool] = Query(None, description="Filter by attendance status: true=present, false=absent"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # Only attendance-incharge is allowed
    if current_user.role != UserRole.attendance_incharge:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Load user with assigned classes and their students + class_name_ref
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.assigned_classes)
            .selectinload(Class.students),        # load students
            selectinload(User.assigned_classes)
            .selectinload(Class.class_name_ref)   # load class name
        )
        .where(User.id == current_user.id)
    )

    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    if not staff.assigned_classes:
        return AttendanceStaffResponse(
            staff_id=str(current_user.id),
            staff_name=current_user.staff_name or "",
            staff_gender=staff.gender,
            assigned_classes_count=0,
            classes=[]
        )

    response_data: List[ClassInfoWithStudents] = []

    for c in staff.assigned_classes:
        # Filter students by staff gender and optional present/absent
        filtered_students = [
            StudentInfo(
                student_id=str(s.id),
                roll_number=s.roll_number,
                name=s.name,
                gender=s.gender,
                present=s.present
            )
            for s in c.students
            if s.gender == staff.gender and (present is None or s.present == present)
        ]

        response_data.append(
            ClassInfoWithStudents(
                class_id=str(c.id),
                class_name=c.class_name_ref.name,
                department=c.department,
                section=c.section,
                regular_or_self=c.regular_or_self,
                students_count=len(filtered_students),
                students=filtered_students
            )
        )

    return AttendanceStaffResponse(
        staff_id=str(current_user.id),
        staff_name=staff.staff_name or "",
        staff_gender=staff.gender,
        assigned_classes_count=len(staff.assigned_classes),
        classes=response_data
    )