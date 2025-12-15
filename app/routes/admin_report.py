from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
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

@router.get("/present-students/pdf", dependencies=[Depends(is_admin)])
async def generate_present_students_pdf(
    db: AsyncSession = Depends(get_db)
):
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
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = []

    # -------------------------
    # Title
    # -------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=1,
        textColor=colors.darkblue
    )

    elements.append(Paragraph("Present Students Report", title_style))
    elements.append(Spacer(1, 20))

    # -------------------------
    # Loop classes
    # -------------------------
    for cls in classes:
        student_stmt = select(Student).where(
            Student.class_id == cls.id,
            Student.present == True
        )
        student_result = await db.execute(student_stmt)
        students = student_result.scalars().all()

        if not students:
            continue

        # Class info box
        class_info = f"""
        <b>Class:</b> {cls.class_name_ref.name} &nbsp;&nbsp;
        <b>Program:</b> {cls.program_type_ref.type_name} &nbsp;&nbsp;
        <b>Dept:</b> {cls.department or '-'} &nbsp;&nbsp;
        <b>Section:</b> {cls.section or '-'}
        """

        elements.append(Paragraph(class_info, styles["Normal"]))
        elements.append(Spacer(1, 8))

        # Table data
        table_data = [["Roll No", "Student Name", "Gender"]]

        for s in students:
            table_data.append([
                s.roll_number,
                s.name,
                s.gender
            ])

        table = Table(
            table_data,
            colWidths=[90, 260, 90],
            repeatRows=1
        )

        table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5597")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),

            # Body
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),

            # Alternate row color
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 25))

    if not elements:
        raise HTTPException(
            status_code=404,
            detail="No present students found"
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