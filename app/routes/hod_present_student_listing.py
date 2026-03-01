from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserRole,User,Class
from app.auth.dependencies import get_current_user
from app.database import get_db



from fastapi.responses import StreamingResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import Table
import io


router=APIRouter(
    prefix="/hod",
    tags=["HOD Endpoints"]
)



@router.get("/list-present-students")
async def list_present_students_for_hod(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 🔐 Allow only HOD role
    role_names = [role.name for role in current_user.roles]

    if UserRole.hod not in role_names:
        raise HTTPException(status_code=403, detail="HOD access required")

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.assigned_classes)
            .selectinload(Class.students),
            selectinload(User.assigned_classes)
            .selectinload(Class.class_name_ref)
        )
        .where(User.id == current_user.id)
    )

    hod = result.scalars().first()

    if not hod:
        raise HTTPException(status_code=404, detail="User not found")

    if not hod.assigned_classes:
        return {
            "message": "No classes assigned",
            "classes": []
        }

    response_data = []

    for cls in hod.assigned_classes:

        present_students = [
            {
                "student_id": str(student.id),
                "roll_number": student.roll_number,
                "name": student.name,
                "gender": student.gender,
                "present": student.present
            }
            for student in sorted(
                cls.students,
                key=lambda s: s.roll_number or ""
            )
            if student.present is True
        ]

        # ✅ Dynamic department message
        dynamic_message = (
            "Mr. President / Mr. Principal / Mr. Secretary to Government of India, "
            "Ministry of Earth Sciences, New Delhi. "
            f"I present unto you the candidates IN PERSON in the Department of {cls.class_name_ref.name} "
            "who have been certified after examination to be duly qualified to receive "
            "the degrees of Madurai Kamaraj University."
        )

        response_data.append({
            "class_id": str(cls.id),
            "class_name": cls.class_name_ref.name if cls.class_name_ref else None,
            "department": cls.department,
            "section": cls.section,
            "regular_or_self": cls.regular_or_self,
            "students_count": len(present_students),
            "message": dynamic_message,  # 🔥 Added here
            "students": present_students
        })

    return {
        "hod_id": str(hod.id),
        "hod_name": hod.staff_name,
        "assigned_classes_count": len(hod.assigned_classes),
        "classes": response_data
    }


@router.get("/download-present-students-pdf")
async def download_present_students_pdf(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # 🔐 HOD Role Check
    role_names = [role.name for role in current_user.roles]
    if UserRole.hod not in role_names:
        raise HTTPException(status_code=403, detail="HOD access required")

    # 🔹 Load HOD with classes + students
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.assigned_classes)
            .selectinload(Class.students),
            selectinload(User.assigned_classes)
            .selectinload(Class.class_name_ref)
        )
        .where(User.id == current_user.id)
    )

    hod = result.scalars().first()

    if not hod:
        raise HTTPException(status_code=404, detail="User not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # 🔷 Title
    elements.append(
        Paragraph(f"Present Students Report - {hod.staff_name}", styles["Title"])
    )
    elements.append(Spacer(1, 0.3 * inch))

    for cls in hod.assigned_classes:

        present_students = sorted(
            [s for s in cls.students if s.present is True],
            key=lambda s: s.roll_number or ""
        )

        # 🔷 Class Header
        class_title = f"""
        Class: {cls.class_name_ref.name if cls.class_name_ref else ''} |
        Dept: {cls.department} |
        Section: {cls.section} |
        Type: {cls.regular_or_self}
        """
        elements.append(Paragraph(class_title, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        # ✅ Table Header (Gender removed)
        data = [["S.No", "Roll No", "Name"]]

        # ✅ Add Serial Numbers
        for index, student in enumerate(present_students, start=1):
            data.append([
                index,
                student.roll_number,
                student.name
            ])

        if len(present_students) == 0:
            data.append(["-", "-", "No Present Students"])

        # ✅ Proper column widths for 3 columns
        table = Table(
            data,
            colWidths=[50, 100, 250],
            repeatRows=1
        )

        table.setStyle(TableStyle([
    # 🔷 Header - Blue Background
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E79")),  # Dark Blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # 🔷 Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#1F4E79")),

        # 🔷 Column Alignment
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Roll No
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Name

        # 🔷 Body Styling
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E7F0FA")),  # Light Blue Rows
    ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=present_students_report.pdf"
        },
    )