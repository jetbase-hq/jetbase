# Configuration ⚙️

## Configuration Options

| Option | Environment Variable | Allowed Values | Default |
|--------|---------------------|----------------|---------|
| `sqlalchemy_url` | `JETBASE_SQLALCHEMY_URL` | SQLAlchemy connection string | *(required)* |
| `postgres_schema` | `JETBASE_POSTGRES_SCHEMA` | Any valid schema name | `None` (uses `public`) |
| `skip_validation` | `JETBASE_SKIP_VALIDATION` | `True` / `False` | `False` |
| `skip_checksum_validation` | `JETBASE_SKIP_CHECKSUM_VALIDATION` | `True` / `False` | `False` |
| `skip_file_validation` | `JETBASE_SKIP_FILE_VALIDATION` | `True` / `False` | `False` |
| `snowflake_private_key` | `JETBASE_SNOWFLAKE_PRIVATE_KEY` | PEM/multi-line string | `None` |
| `snowflake_private_key_password` | `JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD` | password string | `None` |


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

=== "MySQL"

    ```python
    sqlalchemy_url = "mysql+pymysql://username:password@host:port/database"
    ```

=== "SQLite"

    ```python
    sqlalchemy_url = "sqlite:///path/to/database.db"
    ```

=== "Snowflake"

    ```python
    sqlalchemy_url = "snowflake://username:password@account/database/schema?warehouse=WAREHOUSE"
    ```

=== "Databricks"

    ```python
    sqlalchemy_url = "databricks://token:<ACCESS_TOKEN>@hostname?http_path=<HTTP_PATH>&catalog=<CATALOG>&schema=<SCHEMA>"
    ```


### `postgres_schema` 
**Optional (even for PostgreSQL databases)**

Specify a PostgreSQL schema to use for migrations if using a PostgreSQL database. If not set, uses the default `public` schema.

```python
postgres_schema = "my_schema"
```

### `skip_checksum_validation` 
**(Optional)**

Skips [checksum validations](validations/index.md#checksum-validation)

```python
skip_checksum_validation = False  # Default
```

!!! warning "When to use this"
Only set this to `True` if you intentionally modified a migration file and want to skip the checksum check. It's generally better to use `jetbase fix-checksums` instead.

### `skip_file_validation` 
**(Optional)**

Skip file validations (see [File Validations](validations/index.md#file-validations) for details).

```python
skip_file_validation = False  # Default
```

### `skip_validation` 
**(Optional)**

Skips both checksum and file validation checks when running migrations. See [Validation Types](validations/index.md#validation-types) for details. **Use with caution!**

```python
skip_validation = False  # Default
```

When set to `True`, skips both checksum and file validation.


### `snowflake_private_key` 
**(Optional, for Snowflake key pair authentication)**

This is only needed if connecting to Snowflake and you're using private key authentication instead of username/password.

```bash
export JETBASE_SNOWFLAKE_PRIVATE_KEY="""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFA...
-----END PRIVATE KEY-----"""
```

!!! tip
    It's best to use environment variable for this and read your private key file in as the environment variable.
    ```bash
    export JETBASE_SNOWFLAKE_PRIVATE_KEY=$(cat snowflake_private_key.pem)
    ```

### `snowflake_private_key_password`  
**(Optional, for encrypted keys)**

The password to decrypt your PEM-encoded private key if it is password-protected.

```python
export SNOWFLAKE_PRIVATE_KEY_PASSWORD=my-secret-password
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
