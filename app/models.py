import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Boolean, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

staff_classes = Table(
    "staff_classes",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("class_id", UUID(as_uuid=True), ForeignKey("classes.id"))
)

class UserRole(str, enum.Enum):
    admin = "admin"
    certificate_incharge = "certificate_incharge"
    attendance_incharge = "attendance_incharge"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    staff_roll_number = Column(String, unique=True, nullable=True)
    staff_name = Column(String, nullable=True)

    role = Column(Enum(UserRole), nullable=False)

    gender = Column(Enum("male", "female", name="staff_gender_enum"), nullable=False)

    assigned_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)

    assigned_classes = relationship(
        "Class",
        secondary=staff_classes,
        back_populates="assigned_staff"
    )


class ClassName(Base):
    __tablename__ = "class_names"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    classes = relationship("Class", back_populates="class_name_ref")


class ProgramType(Base):
    __tablename__ = "program_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String, unique=True, nullable=False)

    classes = relationship("Class", back_populates="program_type_ref")


class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_name_id = Column(UUID(as_uuid=True), ForeignKey("class_names.id"), nullable=False)
    class_name_ref = relationship("ClassName", back_populates="classes")

    program_type_id = Column(UUID(as_uuid=True), ForeignKey("program_types.id"), nullable=False)
    program_type_ref = relationship("ProgramType", back_populates="classes")

    department = Column(String, nullable=True)
    section = Column(String, nullable=True)
    regular_or_self = Column(String, nullable=True)

    students = relationship("Student", 
                            back_populates="class_ref",
                            order_by="Student.roll_number")
    assigned_staff = relationship(
        "User",
        secondary=staff_classes,
        back_populates="assigned_classes"
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roll_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    gender = Column(Enum("male", "female", name="gender_enum"), nullable=False)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    class_ref = relationship("Class", back_populates="students")

    present = Column(Boolean, nullable=False, default=False)
