from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Student,UserRole
from app.helpers.attendance_time_checker import check_attendance_time_limit
from app.schemas.attendance_marking import MarkAttendanceResponse

router = APIRouter(prefix="/attendance-staff", tags=["Attendance Incharge Marking Attendances"])

# -------------------------
# PUT: Mark Attendance
# -------------------------
@router.put("/mark-attendace", response_model=MarkAttendanceResponse)
async def mark_attendance(
    student_id: str,
    present: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # 1️⃣ Load full user with roles + assigned classes
    user_result = await db.execute(
        select(User)
        .options(
            selectinload(User.roles),              # ✅ load roles
            selectinload(User.assigned_classes)   # ✅ load classes
        )
        .where(User.id == current_user.id)
    )
    staff = user_result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    # 2️⃣ Proper role check (many-to-many)
    has_attendance_role = any(
        role.name == UserRole.attendance_incharge
        for role in staff.roles
    )

    if not has_attendance_role:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 3️⃣ Time limit check
    check_attendance_time_limit()

    # 4️⃣ Validate student UUID
    try:
        student_uuid = UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid student_id format")

    # 5️⃣ Fetch student WITH class
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.class_ref))
        .where(Student.id == student_uuid)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 6️⃣ Check assigned class access
    assigned_class_ids = {c.id for c in staff.assigned_classes}

    if student.class_id not in assigned_class_ids:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this student's class"
        )

    # 7️⃣ Gender restriction logic
    if not staff.can_handle_both_genders:
        if student.gender != staff.gender:
            raise HTTPException(
                status_code=403,
                detail="You can mark attendance only for same-gender students"
            )

    # 8️⃣ Update attendance
    student.present = present
    await db.commit()
    await db.refresh(student)

    return {
        "message": "Attendance updated successfully",
        "student_id": student_id,
        "student_name": student.name,
        "present": student.present
    }
