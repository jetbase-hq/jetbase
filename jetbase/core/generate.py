import os
from datetime import datetime


def generate_new_migration_file_cmd(description: str | None = None) -> None:
    migrations_dir: str = os.path.join(os.getcwd(), "migrations")
    if not os.path.exists(migrations_dir):
        print(
            "Migrations directory not found. Run 'jetbase initialize' to set up jetbase.\n If you have already done so, run this command from the jetbase directory."
        )
        return

    if description is None:
        print("Error: description is required")
        return

    timestamp = datetime.now().strftime("%Y%m%d.%H%M%S")
    filename: str = f"V{timestamp}__{description.replace(' ', '_')}.sql"
    filepath: str = os.path.join(migrations_dir, filename)

    with open(filepath, "w") as f:  # noqa: F841
        pass
    print(f"Created migration file: {filepath}")
