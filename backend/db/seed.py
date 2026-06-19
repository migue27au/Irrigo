from db.db import SessionLocal
from models.user import User
from core.security import hash_password

# docker compose exec backend python -m db.seed

def run():
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin"),
                name="Admin",
                role="admin"
            )
            db.add(admin)

        test = db.query(User).filter_by(username="test").first()
        if not test:
            test = User(
                username="test",
                password_hash=hash_password("secret123"),
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