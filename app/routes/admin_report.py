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
from app.models import Class, Student,ProgramType,ClassName
from app.auth.dependencies import is_admin

router = APIRouter(
    prefix="/admin/reports",
    tags=["Reports"]
    )


@router.get("/present-students/pdf", dependencies=[Depends(is_admin)])
async def generate_present_students_pdf(
    db: AsyncSession = Depends(get_db),
    program_type: str | None = None
):
    # -------------------------
    # Fetch classes
    # -------------------------
    stmt = (
        select(Class)
        .join(Class.program_type_ref)
        .join(Class.class_name_ref)
        .options(
            selectinload(Class.program_type_ref),
            selectinload(Class.class_name_ref),
        )
        .order_by(ClassName.name)
    )

    if program_type:
        stmt = stmt.where(ProgramType.type_name == program_type.upper())

    result = await db.execute(stmt)
    classes = result.scalars().all()

    if not classes:
        raise HTTPException(status_code=404, detail="No classes found")

    # -------------------------
    # Group classes
    # -------------------------
    pg_classes = []
    ug_classes = []

    for cls in classes:
        if cls.program_type_ref.type_name == "PG":
            pg_classes.append(cls)
        elif cls.program_type_ref.type_name == "UG":
            ug_classes.append(cls)

    # -------------------------
    # PDF Setup
    # -------------------------
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
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

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=20,
        spaceAfter=10
    )

    elements.append(Paragraph("Present Students Report", title_style))
    elements.append(Spacer(1, 20))

    # -------------------------
    # Function to render class tables
    # -------------------------
    async def render_classes(class_list):
        for cls in class_list:
            student_stmt = select(Student).where(
                Student.class_id == cls.id,
                Student.present.is_(True)
            )
            student_result = await db.execute(student_stmt)
            students = student_result.scalars().all()

            if not students:
                continue

            # Class info (NO program here)
            class_info = f"""
            <b>Class:</b> {cls.class_name_ref.name} &nbsp;&nbsp;
            <b>Section:</b> {cls.section or '-'}
            """

            elements.append(Paragraph(class_info, styles["Normal"]))
            elements.append(Spacer(1, 8))

            table_data = [["Roll No", "Student Name"]]
            for s in students:
                table_data.append([s.roll_number, s.name])

            table = Table(
                table_data,
                colWidths=[90, 260, 90],
                repeatRows=1
            )

            table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5597")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Roll No
            ("ALIGN", (1, 1), (1, -1), "LEFT"),    # Student Name

            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ]))


            elements.append(table)
            elements.append(Spacer(1, 25))

    # -------------------------
    # Render PG section
    # -------------------------
    if (not program_type or program_type.upper() == "PG") and pg_classes:
        elements.append(Paragraph("PG Classes", section_style))
        await render_classes(pg_classes)

    # -------------------------
    # Render UG section
    # -------------------------
    if (not program_type or program_type.upper() == "UG") and ug_classes:
        elements.append(Paragraph("UG Classes", section_style))
        await render_classes(ug_classes)

    if len(elements) <= 2:
        raise HTTPException(status_code=404, detail="No present students found")

    # -------------------------
    # Build PDF
    # -------------------------
    pdf.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=present_students_report.pdf"
        }
    )
