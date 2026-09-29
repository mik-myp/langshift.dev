"""Operator-only CLI. No password/token arguments, environment defaults or output."""
import argparse
from getpass import getpass
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from db import SessionLocal, engine
from security import provision_user, set_active


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create-user", "disable", "enable"])
    parser.add_argument("login")
    args = parser.parse_args()
    try:
        if args.action == "create-user":
            password = getpass("New password (15..128 characters): ")
            confirmation = getpass("Confirm password: ")
            if password != confirmation:
                raise ValueError("Passwords do not match")
            with SessionLocal.begin() as session:
                user = provision_user(session, args.login, password)
                identity = user.id
            print(f"User provisioned: id={identity}; no credential printed")
        else:
            with SessionLocal.begin() as session:
                set_active(session, args.login, args.action == "enable")
            print("Account state changed; all earlier sessions remain invalid")
    except (ValueError, ValidationError, SQLAlchemyError):
        # Even ValidationError.__str__ may contain submitted input.
        print("Operation rejected; check account state/password policy/database readiness")
        raise SystemExit(1) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
