import argparse
import os
import sys

from app.core.config import settings
from app.startup.admin_bootstrap import AdminBootstrapConfig, bootstrap_admin_account
from app.startup.migarate import DatabaseMigrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or promote a first-run admin account."
    )
    parser.add_argument("--email", default=os.getenv("BOOTSTRAP_ADMIN_EMAIL"))
    parser.add_argument("--username", default=os.getenv("BOOTSTRAP_ADMIN_USERNAME"))
    parser.add_argument("--password", default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"))
    parser.add_argument("--full-name", dest="full_name", default=os.getenv("BOOTSTRAP_ADMIN_FULL_NAME", "Administrator"))
    parser.add_argument("--role", default=os.getenv("BOOTSTRAP_ADMIN_ROLE", "super_admin"))
    parser.add_argument("--reset-password", action="store_true")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    missing = []
    if not args.email:
        missing.append("--email or BOOTSTRAP_ADMIN_EMAIL")
    if not args.username:
        missing.append("--username or BOOTSTRAP_ADMIN_USERNAME")
    if not args.password:
        missing.append("--password or BOOTSTRAP_ADMIN_PASSWORD")
    if missing:
        raise SystemExit(f"Missing required values: {', '.join(missing)}")


def main() -> int:
    args = parse_args()
    validate_args(args)

    DatabaseMigrator(settings.get_database_url).run_migrations()
    _, message = bootstrap_admin_account(
        AdminBootstrapConfig(
            email=args.email,
            username=args.username,
            password=args.password,
            full_name=args.full_name,
            role=args.role,
            reset_password=args.reset_password,
        )
    )
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
