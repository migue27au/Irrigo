from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password


async def create_admin_user(db: AsyncSession):
    """
    Creates a default admin user if it does not exist.
    Used for initial development setup.
    """

    admin_email = "admin@admin.com"
    admin_password = "admin"

    result = await db.execute(
        select(User).where(User.email == admin_email)
    )

    admin = result.scalar_one_or_none()

    if admin:
        print("Admin already exists")
        return

    new_admin = User(
        email=admin_email,
        password_hash=hash_password(admin_password),
        name="System Admin",
        role="admin"
    )

    db.add(new_admin)
    await db.commit()

    print("Admin user created successfully")