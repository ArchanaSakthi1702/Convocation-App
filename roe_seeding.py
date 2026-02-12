import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Role, UserRole


async def seed_roles():
    async with AsyncSessionLocal() as session:

        for role_enum in UserRole:
            # Check if role already exists
            result = await session.execute(
                select(Role).where(Role.name == role_enum)
            )
            existing_role = result.scalars().first()

            if not existing_role:
                new_role = Role(name=role_enum)
                session.add(new_role)
                print(f"✅ Created role: {role_enum.value}")
            else:
                print(f"ℹ️ Role already exists: {role_enum.value}")

        await session.commit()

    print("\n🎉 Role seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_roles())
