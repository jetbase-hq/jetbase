import argparse

from jetbase.core.initialize import initilize_jetbase
from jetbase.core.rollback import rollback
from jetbase.core.upgrade import upgrade


def main() -> None:
    parser = argparse.ArgumentParser(description="Jetbase CLI")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("init", help="Initialize jetbase in current directory")
    subparsers.add_parser("upgrade", help="Execute pending migrations")
    subparsers.add_parser("rollback", help="Rollback migration(s)")

    args = parser.parse_args()

    if args.command == "init":
        initilize_jetbase()
    elif args.command == "upgrade":
        upgrade()
    elif args.command == "rollback":
        rollback()
