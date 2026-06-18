from backend.db.db import SessionLocal
from backend.models.user import User
from backend.core.security import get_password_hash


def run():
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(email="admin@admin.com").first()
        if not admin:
            admin = User(
                email="admin@admin.com",
                password_hash=get_password_hash("admin"),
                name="Admin",
                role="admin"
            )
            db.add(admin)

        test = db.query(User).filter_by(email="test@test.com").first()
        if not test:
            test = User(
                email="test@test.com",
                password_hash=get_password_hash("secret123"),
                name="Test",
                role="user"
            )
            db.add(test)

        db.commit()

        print("Seed completed")

    finally:
        db.close()


if __name__ == "__main__":
    run()