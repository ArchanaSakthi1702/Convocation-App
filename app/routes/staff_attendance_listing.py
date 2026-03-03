from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional,List

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Class, UserRole,SeatingPlan
from app.schemas.listing_for_attendance import AttendanceStaffResponse,ClassInfoWithStudents,StudentInfo
from app.schemas.seating import SeatingInfo



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

    # 🔹 Load full user with roles + assigned classes + students
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.roles),
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

    # 🔹 Role check
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

        # 🔹 Gender filtering for students
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

        # 🔹 Fetch seating plans for this class (NO model change)
        seating_result = await db.execute(
            select(SeatingPlan).where(
                SeatingPlan.class_id == c.id
            )
        )

        all_seating = seating_result.scalars().all()

        # 🔹 Gender filtering for seating
        if staff.can_handle_both_genders:
            seating_filtered = all_seating
        else:
            seating_filtered = [
                sp for sp in all_seating
                if sp.gender == staff.gender
            ]

        seating_data = [
            SeatingInfo(
                gender=sp.gender,
                chair_from=sp.chair_from,
                chair_to=sp.chair_to
            )
            for sp in seating_filtered
        ]

        response_data.append(
            ClassInfoWithStudents(
                class_id=str(c.id),
                class_name=c.class_name_ref.name if c.class_name_ref else None,
                department=c.department,
                section=c.section,
                regular_or_self=c.regular_or_self,
                students_count=len(filtered_students),
                students=filtered_students,
                seating=seating_data
            )
        )

    return AttendanceStaffResponse(
        staff_id=str(staff.id),
        staff_name=staff.staff_name or "",
        staff_gender=staff.gender,
        assigned_classes_count=len(staff.assigned_classes),
        classes=response_data
    )