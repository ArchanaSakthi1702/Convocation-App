from pydantic import BaseModel


class ClassCreate(BaseModel):
    class_name: str
    program_type: str  # UG / PG
    department: str = None
    section: str = None
    regular_or_self: str = None  # "Regular" / "Self-Financed"
