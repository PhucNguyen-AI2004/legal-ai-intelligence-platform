"""Promote an existing account: python -m app.scripts.promote_user --email ..."""
import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def promote_user(db: Session, email: str) -> bool:
    user = db.scalar(select(User).where(User.email == email.strip().lower()).with_for_update())
    if user is None:
        return False
    user.role = "admin"
    db.commit()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote an existing user to admin.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    # Import configured connection only for explicit command execution.
    from app.db.session import SessionLocal
    try:
        with SessionLocal() as db:
            found = promote_user(db, args.email)
        print("Admin role confirmed." if found else "User not found. No account created.")
        return 0 if found else 1
    except Exception:
        # Connection exceptions can contain credentials; never print them.
        print("Promotion failed. Check database access and migration status.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
