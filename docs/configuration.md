# Configuration ⚙️

## Configuration Options

| Option | Environment Variable | Allowed Values | Default |
|--------|---------------------|----------------|---------|
| `sqlalchemy_url` | `JETBASE_SQLALCHEMY_URL` | SQLAlchemy connection string | *(required)* |
| `postgres_schema` | `JETBASE_POSTGRES_SCHEMA` | Any valid schema name | `None` (uses `public`) |
| `skip_validation` | `JETBASE_SKIP_VALIDATION` | `True` / `False` | `False` |
| `skip_checksum_validation` | `JETBASE_SKIP_CHECKSUM_VALIDATION` | `True` / `False` | `False` |
| `skip_file_validation` | `JETBASE_SKIP_FILE_VALIDATION` | `True` / `False` | `False` |

---

Jetbase uses a simple Python configuration file (`env.py`) to manage your database connection and behavior settings.

For flexibility, you can also set config options as environment variables, in `jetbase.toml`, or in `pyproject.toml`.

## Configuration Sources

Jetbase loads configuration from four sources, checked in the following priority order:

| Priority | Source | Location |
|:--------:|--------|----------|
| 1 | `env.py` | `jetbase/env.py` |
| 2 | Environment variables | `JETBASE_{OPTION_NAME}` ([see example](#example-setting-sqlalchemy_url)) |
| 3 | `jetbase.toml` | `jetbase/jetbase.toml` (file must be manually created)  |
| 4 | `pyproject.toml` | `[tool.jetbase]` section |

The first source that defines a value wins. For example, if `sqlalchemy_url` is set in both `env.py` and as an environment variable, the `env.py` value is used.

### Example: Setting `sqlalchemy_url`

=== "env.py"

    ```python
    # jetbase/env.py
    sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
    ```

=== "Environment Variable"

    ```bash
    export JETBASE_SQLALCHEMY_URL="postgresql://user:password@localhost:5432/mydb"
    ```

=== "jetbase.toml"

    ```toml
    # jetbase/jetbase.toml
    sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
    ```

=== "pyproject.toml"

    ```toml
    # pyproject.toml
    [tool.jetbase]
    sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
    ```



### `sqlalchemy_url` (Required)

The database connection string in SQLAlchemy format.

=== "PostgreSQL"

    ```python
    sqlalchemy_url = "postgresql://username:password@host:port/database"
    ```


### `postgres_schema` (Optional, even if using a PostgreSQL database)

Specify a PostgreSQL schema to use for migrations if using a PostgreSQL database. If not set, uses the default `public` schema.

```python
postgres_schema = "my_schema"
```

### `skip_checksum_validation` (Optional)

Skips [checksum validations](validations/index.md#checksum-validation)

```python
skip_checksum_validation = False  # Default
```

!!! warning "When to use this"
Only set this to `True` if you intentionally modified a migration file and want to skip the checksum check. It's generally better to use `jetbase fix-checksums` instead.

### `skip_file_validation` (Optional)

Skip file validations (see [File Validations](validations/index.md#file-validations) for details).

```python
skip_file_validation = False  # Default
```

### `skip_validation` (Optional)

Skips both checksum and file validation checks when running migrations. See [Validation Types](validations/index.md#validation-types) for details. **Use with caution!**

```python
skip_validation = False  # Default
```

When set to `True`, skips both checksum and file validation.

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

## Database Tables

Jetbase creates two tables in your database to track migrations:

| Table                | Purpose                                                         |
| -------------------- | --------------------------------------------------------------- |
| `jetbase_migrations` | Stores migration history (version, checksum, applied timestamp) |
| `jetbase_lock`       | Prevents concurrent migrations from running                     |

These tables are created automatically when you run your first migration.
