import asyncio
import getpass
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.auth.security import get_password_hash

async def create_admin(username: str, password: str):
    async with AsyncSessionLocal() as session:
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,                # set username as email
            password=hashed_password,
            role=UserRole.admin,
            gender="male"                  # required field, can be default
        )
        session.add(admin_user)
        await session.commit()

    print(f"✅ Admin user '{username}' created successfully.")

if __name__ == "__main__":
    username = input("Enter admin username: ")
    password = getpass.getpass("Enter admin password: ")
    asyncio.run(create_admin(username, password))
