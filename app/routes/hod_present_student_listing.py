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

    from collections import defaultdict

    grouped_classes = defaultdict(list)

    # Group classes by class_name
    for cls in hod.assigned_classes:
        if cls.class_name_ref:
            grouped_classes[cls.class_name_ref.name].append(cls)

    response_data = []

    for class_name, class_group in grouped_classes.items():

        # Take first class as reference for common fields
        first_class = class_group[0]

        all_students = []
        for cls in class_group:
            all_students.extend(cls.students)

        # Female first sorting
        present_students = [
            {
                "student_id": str(student.id),
                "roll_number": student.roll_number,
                "name": student.name,
                "gender": student.gender,
                "present": student.present
            }
            for student in sorted(
                all_students,
                key=lambda s: (s.gender != "female", s.roll_number or "")
            )
            if student.present is True
        ]

        dynamic_message = (
            "Mr. President / Mr. Principal / Mr. Secretary to Government of India, "
            "Ministry of Earth Sciences, New Delhi. "
            f"I present unto you the candidates IN PERSON in the Department of {class_name} "
            "who have been certified after examination to be duly qualified to receive "
            "the degrees of Madurai Kamaraj University."
        )

        response_data.append({
            # 🔥 Keep SAME structure as first API
            "class_id": str(first_class.id),  # representative id
            "class_name": class_name,
            "department": first_class.department,
           "section": ", ".join(
                sorted(
                    {cls.section for cls in class_group if cls.section}
                )
            ) or None,  # combine sections
            "regular_or_self": first_class.regular_or_self,
            "students_count": len(present_students),
            "message": dynamic_message,
            "students": present_students
        })

    return {
        "hod_id": str(hod.id),
        "hod_name": hod.staff_name,
        "assigned_classes_count": len(grouped_classes),
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

    # 🔹 Load HOD with classes + students + class name
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
        raise HTTPException(status_code=404, detail="No classes assigned")

    # 🔹 PDF Setup
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # 🔷 Title
    elements.append(
        Paragraph(f"Present Students Report - {hod.staff_name}", styles["Title"])
    )
    elements.append(Spacer(1, 0.3 * inch))

    # 🔹 Group Classes by class_name
    from collections import defaultdict

    grouped_classes = defaultdict(list)

    for cls in hod.assigned_classes:
        if cls.class_name_ref:
            grouped_classes[cls.class_name_ref.name].append(cls)

    # 🔹 Loop grouped classes
    for class_name, class_group in grouped_classes.items():

        first_class = class_group[0]

        # 🔹 Combine students from all sections
        all_students = []
        for cls in class_group:
            all_students.extend(cls.students)

        # 🔹 Filter present students + Female first sorting
        present_students = sorted(
            [s for s in all_students if s.present is True],
            key=lambda s: (s.gender != "female", s.roll_number or "")
        )

        # 🔷 Merge Sections safely
        sections = ", ".join(
            sorted({cls.section for cls in class_group if cls.section})
        ) or "-"

        # 🔷 Class Header
        class_title = f"""
        Class: {class_name} |
        Section: {sections} |
        Type: {first_class.regular_or_self}
        """

        elements.append(Paragraph(class_title, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        # 🔷 Dynamic Message (Single per class name)
        dynamic_message = (
            "Mr. President / Mr. Principal / Mr. Secretary to Government of India, "
            "Ministry of Earth Sciences, New Delhi. "
            f"I present unto you the candidates IN PERSON in the Department of "
            f"{class_name} "
            "who have been certified after examination to be duly qualified to receive "
            "the degrees of Madurai Kamaraj University."
        )

        elements.append(Paragraph(dynamic_message, styles["Normal"]))
        elements.append(Spacer(1, 0.3 * inch))

        # 🔷 Table Header
        data = [["S.No", "Roll No", "Name"]]

        for index, student in enumerate(present_students, start=1):
            data.append([
                index,
                student.roll_number,
                student.name
            ])

        if len(present_students) == 0:
            data.append(["-", "-", "No Present Students"])

        # 🔷 Create Table
        table = Table(
            data,
            colWidths=[50, 100, 250],
            repeatRows=1
        )

        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#1F4E79")),

            # Column alignment
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),

            # Body styling
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E7F0FA")),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))

    # 🔹 Build PDF
    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=present_students_report.pdf"
        },
    )