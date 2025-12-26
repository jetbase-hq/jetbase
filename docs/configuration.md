# Configuration ⚙️

Jetbase uses a simple Python configuration file (`env.py`) to manage your database connection and behavior settings.

## Configuration File

When you run `jetbase init`, it creates a `jetbase/env.py` file with default settings:

```python
# Jetbase Configuration
# Update the sqlalchemy_url with your database connection string.

sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
```

## Configuration Options

### `sqlalchemy_url` (Required)

The database connection string in SQLAlchemy format.

=== "PostgreSQL"

    ```python
    sqlalchemy_url = "postgresql://username:password@host:port/database"
    ```

    **Examples:**
    ```python
    # Local database
    sqlalchemy_url = "postgresql://postgres:mypassword@localhost:5432/myapp"

    # Remote database
    sqlalchemy_url = "postgresql://admin:secret@db.example.com:5432/production"

    # With SSL
    sqlalchemy_url = "postgresql://user:pass@host:5432/db?sslmode=require"
    ```

=== "SQLite"

    ```python
    # Relative path (from jetbase directory)
    sqlalchemy_url = "sqlite:///mydb.sqlite"

    # Absolute path
    sqlalchemy_url = "sqlite:////home/user/databases/myapp.db"

    # In-memory (for testing)
    sqlalchemy_url = "sqlite:///:memory:"
    ```

### `postgres_schema` (Optional)

Specify a PostgreSQL schema to use for migrations. If not set, uses the default `public` schema.

```python
sqlalchemy_url = "postgresql://user:pass@localhost:5432/mydb"
postgres_schema = "my_custom_schema"
```

### `skip_validation` (Optional)

Skip all validation checks when running migrations. **Use with caution!**

```python
skip_validation = False  # Default
```

When set to `True`, skips both checksum and file validation.

### `skip_checksum_validation` (Optional)

Skip only checksum validation when running migrations.

```python
skip_checksum_validation = False  # Default
```

!!! warning "When to use this"
Only set this to `True` if you intentionally modified a migration file and want to skip the checksum check. It's generally better to use `jetbase fix-checksums` instead.

### `skip_file_validation` (Optional)

Skip file validation (checking if migration files exist).

```python
skip_file_validation = False  # Default
```

## Full Configuration Example

Here's a complete `env.py` with all options:

```python
# Jetbase Configuration

# Database connection (required)
sqlalchemy_url = "postgresql://myuser:mypassword@localhost:5432/myapp_dev"

# PostgreSQL schema (optional, defaults to 'public')
postgres_schema = "migrations"

# Validation settings (all optional, default to False)
skip_validation = False
skip_checksum_validation = False
skip_file_validation = False
```

## Environment-Specific Configuration

You can use environment variables for sensitive data:

```python
import os

sqlalchemy_url = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/mydb"  # fallback for development
)
```

Or use different configurations based on environment:

```python
import os

env = os.getenv("ENV", "development")

if env == "production":
    sqlalchemy_url = os.getenv("DATABASE_URL")
elif env == "staging":
    sqlalchemy_url = "postgresql://user:pass@staging-db:5432/myapp"
else:
    sqlalchemy_url = "postgresql://postgres:postgres@localhost:5432/myapp_dev"
```

## Command-Line Overrides

Some configuration options can be overridden via command-line flags:

```bash
# Skip all validation
jetbase upgrade --skip-validation

# Skip only checksum validation
jetbase upgrade --skip-checksum-validation

# Skip only file validation
jetbase upgrade --skip-file-validation
```

!!! tip
Command-line flags take precedence over configuration file settings.

## Database Tables

Jetbase creates two tables in your database to track migrations:

| Table                | Purpose                                                         |
| -------------------- | --------------------------------------------------------------- |
| `jetbase_migrations` | Stores migration history (version, checksum, applied timestamp) |
| `jetbase_lock`       | Prevents concurrent migrations from running                     |

These tables are created automatically when you run your first migration.

## Next Steps

- [Writing Migrations](migrations/writing-migrations.md) — Learn how to write effective migration files
- [Commands Reference](commands/index.md) — Explore all available commands
