"""D04 disposable first schema only. D05 onward uses Alembic, not create_all."""
from sqlalchemy import select
from db import make_engine, session_factory
from models import Base, User
from services import seed_user


def main():
    engine = make_engine()
    try:
        Base.metadata.create_all(engine)
        with session_factory(engine).begin() as session:
            user_id = session.scalar(select(User.id).where(User.login == "alice"))
            if user_id is None:
                user_id = seed_user(session)
        print(f"alice_id={user_id}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
