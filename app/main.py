from fastapi import FastAPI
from app.database import async_engine as engine, Base
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.routes.admin_login import router as admin_login_router
from app.routes.staff_login import router as staff_login_router
from app.routes.admin_class_creation import router as admin_class_creation_router
from app.routes.admin_staff_creation import router as admin_staff_creation_router
from app.routes.admin_student_creation import router as admin_student_creation_router
from app.routes.admin_program_type_listing import router as admin_program_type_router
from app.routes.admin_students_listing import router as admin_students_listing_router
from app.routes.staff_attendance_listing import router as staff_attendance_listing_router
from app.routes.staff_attendance_marking import router as staff_attendance_marking_router
from app.routes.certificate_staff_listing import router as certificate_staff_router
from app.routes.admin_staff_listing import router as admin_staff_listing_router
from app.routes.admin_staff_deletion import router as admin_staff_deletion_router
from app.routes.admin_report import router as admin_report_router
from app.routes.admin_attendance_certificate_incharge_class_summary import router as summary_router
from app.routes.admin_student_deletion import router as admin_student_deleting_router
from app.routes.admin_student_updation import router as admin_student_updation_router
from app.routes.admin_staff_updation import router as admin_staff_updation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown code (if needed) can go here
    await engine.dispose()



origins = [
    "http://localhost:3000",   # React Dev
    "http://127.0.0.1:3000",
    "http://localhost:5173",   # Vite
    "http://127.0.0.1:5173",
    "*"  # allow all (use only for development)
]

app = FastAPI(
    lifespan=lifespan,
    description="ANJAC Convocation Attendance App"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allowed frontend URLs
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],            # Authorization, Content-Type...
)


@app.get("/")
async def root():
    return {"message": "ANJAC Convocation Attendance System API Running"}


app.include_router(staff_login_router)
app.include_router(admin_login_router)
app.include_router(admin_class_creation_router)
app.include_router(admin_staff_creation_router)
app.include_router(admin_student_creation_router)
app.include_router(admin_program_type_router)
app.include_router(admin_students_listing_router)
app.include_router(staff_attendance_listing_router)
app.include_router(staff_attendance_marking_router)
app.include_router(certificate_staff_router)
app.include_router(admin_staff_listing_router)
app.include_router(admin_staff_deletion_router)
app.include_router(summary_router)
app.include_router(admin_report_router)
app.include_router(admin_student_deleting_router)
app.include_router(admin_student_updation_router)
app.include_router(admin_staff_updation_router)