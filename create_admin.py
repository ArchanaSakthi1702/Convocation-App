import asyncio
import getpass
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import User, Role, UserRole
from app.auth.security import get_password_hash


async def create_admin(username: str, password: str):
    async with AsyncSessionLocal() as session:

        # 🔎 Check if admin role exists
        result = await session.execute(
            select(Role).where(Role.name == UserRole.admin)
        )
        admin_role = result.scalars().first()

        # 🆕 If role does not exist, create it
        if not admin_role:
            admin_role = Role(name=UserRole.admin)
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)

        # 🔐 Hash password
        hashed_password = get_password_hash(password)

        # 👤 Create admin user
        admin_user = User(
            username=username,
            password=hashed_password,
            gender="male",  # required
            roles=[admin_role]   # ✅ many-to-many assignment
        )

        session.add(admin_user)
        await session.commit()

    print(f"✅ Admin user '{username}' created successfully.")


if __name__ == "__main__":
    username = input("Enter admin username: ")
    password = getpass.getpass("Enter admin password: ")
    asyncio.run(create_admin(username, password))
