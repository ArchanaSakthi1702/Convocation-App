# app/routes/student_routes.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.auth.dependencies import is_admin
from app.models import Student, Class
from app.schemas.student_schemas import StudentCreate, StudentBulkCreate
from app.helpers.class_finder_for_students_creation import get_class_object

router = APIRouter(
    prefix="/admin", 
    tags=["Admin Student Creation"],
    dependencies=[Depends(is_admin)]
)




@router.post("/student/create")
async def create_student(payload: StudentCreate, db: AsyncSession = Depends(get_db)):

    # Check roll number exists
    result = await db.execute(select(Student).where(Student.roll_number == payload.roll_number))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Roll number already exists")

    # Resolve class
    cls_obj = None
    if payload.class_id:
        result = await db.execute(select(Class).where(Class.id == UUID(payload.class_id)))
        cls_obj = result.scalars().first()

    else:
        if not (payload.class_name and payload.program_type and payload.department and payload.section):
            raise HTTPException(
                status_code=400,
                detail="Provide either class_id or all class name details"
            )

        cls_obj = await get_class_object(
            db,
            payload.class_name,
            payload.program_type,
            payload.department,
            payload.section
        )

    if not cls_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    # Create student
    new_student = Student(
        roll_number=payload.roll_number,
        name=payload.name,
        gender=payload.gender,
        class_id=cls_obj.id
    )

    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)

    return {
        "message": "Student created",
        "student_id": str(new_student.id)
    }


# ---------------------------- BULK CREATE ---------------------------- #

@router.post("student/bulk-create")
async def create_students_bulk(payload: StudentBulkCreate, db: AsyncSession = Depends(get_db)):

    created = []
    errors = []

    for item in payload.students:

        # Check existing roll number
        result = await db.execute(select(Student).where(Student.roll_number == item.roll_number))
        if result.scalars().first():
            errors.append({"roll_number": item.roll_number, "error": "Roll number exists"})
            continue

        # Resolve class
        cls_obj = None
        if item.class_id:
            result = await db.execute(select(Class).where(Class.id == UUID(item.class_id)))
            cls_obj = result.scalars().first()
        else:
            cls_obj = await get_class_object(
                db,
                item.class_name,
                item.program_type,
                item.department,
                item.section
            )

        if not cls_obj:
            errors.append({"roll_number": item.roll_number, "error": "Class not found"})
            continue

        # Create student
        new_stu = Student(
            roll_number=item.roll_number,
            name=item.name,
            gender=item.gender,
            class_id=cls_obj.id
        )
        db.add(new_stu)
        created.append(new_stu)

    await db.commit()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors
    }