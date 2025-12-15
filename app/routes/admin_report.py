from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Class, Student
from app.auth.dependencies import is_admin

router = APIRouter(
    prefix="/admin/reports",
    tags=["Reports"]
    )

@router.get("/present-students/pdf")
async def generate_present_students_pdf(
    db: AsyncSession = Depends(get_db)
):
    # Fetch all classes with relations
    stmt = (
    select(Class)
    .options(
        selectinload(Class.class_name_ref),
        selectinload(Class.program_type_ref),
    )
)
    result = await db.execute(stmt)
    classes = result.scalars().all()

    if not classes:
        raise HTTPException(status_code=404, detail="No classes found")

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    for cls in classes:
        # Fetch present students of this class
        student_stmt = select(Student).where(
            Student.class_id == cls.id,
            Student.present == True
        )
        student_result = await db.execute(student_stmt)
        students = student_result.scalars().all()

        if not students:
            continue  # skip class if no present students

        # Class heading
        class_title = (
            f"<b>Class:</b> {cls.class_name_ref.name} | "
            f"<b>Program:</b> {cls.program_type_ref.type_name} | "
            f"<b>Dept:</b> {cls.department or '-'} | "
            f"<b>Section:</b> {cls.section or '-'}"
        )

        elements.append(Paragraph(class_title, styles["Heading3"]))
        elements.append(Spacer(1, 10))

        # Table data
        table_data = [["Roll No", "Name", "Gender"]]

        for student in students:
            table_data.append([
                student.roll_number,
                student.name,
                student.gender
            ])

        table = Table(table_data, colWidths=[100, 250, 100])
        elements.append(table)
        elements.append(Spacer(1, 25))

    if not elements:
        raise HTTPException(
            status_code=404,
            detail="No present students found in any class"
        )

    pdf.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=present_students_report.pdf"
        }
    )
