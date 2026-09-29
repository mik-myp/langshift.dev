"""Explicit operator retention operation; not a public endpoint."""
import argparse
from sqlalchemy import delete, func, select
from db import SessionLocal, engine
from models import TaskOperation
from security import utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Delete expired receipts; ends their dedup history")
    args = parser.parse_args()
    try:
        with SessionLocal.begin() as session:
            cutoff = utc_now()
            condition = TaskOperation.expires_at <= cutoff
            count = session.scalar(select(func.count()).select_from(TaskOperation).where(condition))
            if args.apply:
                session.execute(delete(TaskOperation).where(condition))
            print("Expired receipt count:", count, "deleted:" if args.apply else "preview only", bool(args.apply))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
