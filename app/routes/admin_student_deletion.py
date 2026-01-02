# app/routes/student_routes.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.auth.dependencies import is_admin
from app.models import Student

# ---------------- SINGLE STUDENT DELETE ---------------- #
router = APIRouter(
    prefix="/admin", 
    tags=["Admin Student Deletion"],
    dependencies=[Depends(is_admin)]
)

@router.delete("/delete-student/{student_id}", dependencies=[Depends(is_admin)])
async def delete_student(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == UUID(student_id)))
    student = result.scalars().first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    await db.delete(student)
    await db.commit()
    
    return {"message": "Student deleted", "student_id": student_id}


# ---------------- BULK STUDENT DELETE ---------------- #
@router.delete("/bulk-delete-students", dependencies=[Depends(is_admin)])
async def delete_students_bulk(student_ids: list[str], db: AsyncSession = Depends(get_db)):
    deleted = []
    errors = []
    
    for sid in student_ids:
        try:
            result = await db.execute(select(Student).where(Student.id == UUID(sid)))
            student = result.scalars().first()
            if student:
                await db.delete(student)
                deleted.append(sid)
            else:
                errors.append({"student_id": sid, "error": "Not found"})
        except Exception as e:
            errors.append({"student_id": sid, "error": str(e)})
    
    await db.commit()
    
    return {
        "deleted_count": len(deleted),
        "errors": errors
    }