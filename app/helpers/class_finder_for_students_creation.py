from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from app.models import Class, ClassName, ProgramType


async def get_class_object(
    db: AsyncSession,
    class_name: str,
    program_type: str | None = None,
    department: str | None = None,
    section: str | None = None
):
    # Base query
    query = (
        select(Class)
        .join(ClassName, Class.class_name_id == ClassName.id)
        .join(ProgramType, Class.program_type_id == ProgramType.id)
        .where(ClassName.name == class_name)   # class_name is mandatory
    )

    # Add filters ONLY if values are provided
    conditions = []

    if program_type:
        conditions.append(ProgramType.type_name == program_type)

    if department:
        conditions.append(Class.department == department)

    if section:
        conditions.append(Class.section == section)

    # Apply dynamic conditions
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    return result.scalar_one_or_none()
