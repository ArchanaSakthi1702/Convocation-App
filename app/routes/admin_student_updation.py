from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import is_admin
from app.models import Student, Class
from app.schemas.student_schemas import StudentUpdate

router = APIRouter(
    prefix="/admin",
    tags=["Admin Student Update"],
    dependencies=[Depends(is_admin)]
)



@router.patch("/student/update/by-id/{student_id}")
async def update_student_by_id(
    student_id: UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 🔐 Roll number uniqueness check
    if payload.roll_number and payload.roll_number != student.roll_number:
        result = await db.execute(
            select(Student).where(Student.roll_number == payload.roll_number)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Roll number already exists"
            )
        student.roll_number = payload.roll_number

    if payload.name is not None:
        student.name = payload.name

    if payload.gender is not None:
        student.gender = payload.gender

    if payload.present is not None:
        student.present = payload.present

    if payload.class_id is not None:
        result = await db.execute(
            select(Class).where(Class.id == payload.class_id)
        )
        cls = result.scalars().first()
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        student.class_id = cls.id

    await db.commit()
    await db.refresh(student)

    return {
        "message": "Student updated successfully",
        "student_id": str(student.id)
    }


@router.put("/student/update/by-roll/{roll_number}")
async def update_student_by_roll(
    roll_number: str,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Student).where(Student.roll_number == roll_number)
    )
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.roll_number and payload.roll_number != student.roll_number:
        result = await db.execute(
            select(Student).where(Student.roll_number == payload.roll_number)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Roll number already exists"
            )
        student.roll_number = payload.roll_number

    if payload.name is not None:
        student.name = payload.name

    if payload.gender is not None:
        student.gender = payload.gender

    if payload.present is not None:
        student.present = payload.present

    if payload.class_id is not None:
        result = await db.execute(
            select(Class).where(Class.id == payload.class_id)
        )
        cls = result.scalars().first()
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        student.class_id = cls.id

    await db.commit()
    await db.refresh(student)

    return {
        "message": "Student updated successfully",
        "student_id": str(student.id)
    }
