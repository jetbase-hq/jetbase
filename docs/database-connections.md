# Database Connections 🔌

Jetbase supports multiple databases with both synchronous and asynchronous connections. This guide covers how to connect to each supported database and configure async/sync modes.

## Configuration Methods

Jetbase supports two ways to configure your database connection:

### Method 1: Module-level Variables

Define configuration variables directly at module level in `jetbase/env.py`:

```python
sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
async_mode = True
```

### Method 2: get_env_vars() Function (Recommended)

For more complex configurations, define a `get_env_vars()` function that returns a dictionary:

```python
from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")

if ENVIRONMENT == "DEV":
    def get_env_vars():
        return {
            "sqlalchemy_url": "sqlite+aiosqlite:///./egos.db",
            "async_mode": True,
        }
else:
    def get_env_vars():
        return {
            "sqlalchemy_url": "postgresql+asyncpg://user:password@localhost:5432/mydb",
            "async_mode": True,
        }
```

**Benefits of get_env_vars():**
- All configuration logic in one place
- Access to full Python expressions and imports
- Easy to maintain and understand
- Clean separation from other code

---

## Complete env.py Examples

### Example 1: Environment-based Configuration with dotenv

```python
# jetbase/env.py
from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if ENVIRONMENT == "DEV":
    def get_env_vars():
        return {
            "sqlalchemy_url": "sqlite+aiosqlite:///./egos.db",
            "async_mode": True,
        }
else:
    def get_env_vars():
        return {
            "sqlalchemy_url": (
                f"postgresql+asyncpg://"
                f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
                f"@{POSTGRES_HOST}:{POSTGRES_PORT}"
                f"/{POSTGRES_DB}"
            ),
            "async_mode": True,
        }
```

### Example 2: Simple SQLite Configuration

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///./mydb.db"
```

### Example 3: Simple PostgreSQL Configuration

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+psycopg2://myuser:mypassword@localhost:5432/myapp"
postgres_schema = "public"
```

### Example 4: Multi-database with get_env_vars()

```python
# jetbase/env.py
from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")

if ENVIRONMENT == "LOCAL":
    def get_env_vars():
        return {
            "sqlalchemy_url": "sqlite+aiosqlite:///./local.db",
            "async_mode": True,
        }

elif ENVIRONMENT == "DEV":
    def get_env_vars():
        return {
            "sqlalchemy_url": "sqlite+aiosqlite:///./dev.db",
            "async_mode": True,
        }

elif ENVIRONMENT == "STAGING":
    def get_env_vars():
        return {
            "sqlalchemy_url": "postgresql+psycopg2://staging_user:staging_pass@staging-db.example.com:5432/staging_db",
            "async_mode": False,
            "postgres_schema": "public",
        }

else:  # Production
    def get_env_vars():
        return {
            "sqlalchemy_url": "postgresql+asyncpg://prod_user:prod_pass@prod-db.example.com:5432/prod_db",
            "async_mode": True,
            "postgres_schema": "public",
        }
```

### Example 5: With Model Paths for Auto-migration

```python
# jetbase/env.py
from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")

if ENVIRONMENT == "DEV":
    def get_env_vars():
        return {
            "sqlalchemy_url": "sqlite+aiosqlite:///./dev.db",
            "async_mode": True,
            "model_paths": ["../app/models.py"],
        }
else:
    def get_env_vars():
        return {
            "sqlalchemy_url": "postgresql+asyncpg://user:pass@db:5432/app",
            "async_mode": True,
            "model_paths": ["../app/models.py"],
        }
```

### Example 6: SQLite with Checksum Validation Disabled

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///./mydb.db"
skip_checksum_validation = True
skip_file_validation = False
```

---

## Configuration Reference

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `sqlalchemy_url` | str | Database connection URL | Required |
| `async_mode` | bool | Enable async database connections | `False` |
| `postgres_schema` | str | PostgreSQL schema search path | `None` |
| `model_paths` | list[str] | Paths to SQLAlchemy model files | `None` |
| `skip_checksum_validation` | bool | Skip migration file checksum validation | `False` |
| `skip_file_validation` | bool | Skip migration file existence validation | `False` |
| `skip_validation` | bool | Skip all validations | `False` |

## Async and Sync Modes ⚡

Jetbase supports both synchronous and asynchronous database connections.

### Configuration Options

**Option 1: Using async_mode in env.py:**

```python
# jetbase/env.py
sqlalchemy_url = "sqlite+aiosqlite:///mydb.db"
async_mode = True
```

**Option 2: Using ASYNC environment variable:**

```bash
export ASYNC=true   # for async mode
export ASYNC=false  # for sync mode (default)
jetbase status
```

Or per command:

```bash
ASYNC=true jetbase status      # async mode
ASYNC=false jetbase migrate    # sync mode
```

### Sync Mode (Default)

Use sync drivers or async drivers (async suffix is automatically stripped):

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
# or
sqlalchemy_url = "sqlite:///mydb.db"
# or even async URLs (suffix is stripped automatically)
sqlalchemy_url = "postgresql+asyncpg://user:password@localhost:5432/mydb"
```

### Async Mode

Use async drivers:

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+asyncpg://user:password@localhost:5432/mydb"
# or
sqlalchemy_url = "sqlite+aiosqlite:///mydb.db"
```

Enable async mode with `async_mode = True` in your config.

### URL Format Reference

| Database | Sync URL | Async URL |
|----------|----------|-----------|
| PostgreSQL | `postgresql+psycopg2://...` | `postgresql+asyncpg://...` |
| SQLite | `sqlite:///path.db` | `sqlite+aiosqlite:///path.db` |
| Snowflake | `snowflake://...` | Not supported |
| MySQL | `mysql+pymysql://...` | Not supported |
| Databricks | `databricks+connector://...` | Not supported |

!!! note
    Only PostgreSQL and SQLite support async mode. Other databases use sync connections regardless of the `ASYNC` setting.

---

## PostgreSQL

### Installing a Driver

PostgreSQL requires a database driver. Examples:

```bash
pip install psycopg2-binary

pip install "psycopg[binary]"
```

### Connection String

```python
sqlalchemy_url = "postgresql+driver://username:password@host:port/database"
```

### Example

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+psycopg2://myuser:mypassword@localhost:5432/myapp"
```

With a specific schema:

```python
# jetbase/env.py
sqlalchemy_url = "postgresql://myuser:mypassword@localhost:5432/myapp"
postgres_schema = "public"
```

### Async Mode

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+asyncpg://myuser:mypassword@localhost:5432/myapp"
```

Run with async mode:

```bash
ASYNC=true jetbase migrate
```

---

## Snowflake

Snowflake is a cloud-based data warehouse. Jetbase supports both username/password and key pair authentication.

### Installing the Driver

Snowflake requires additional dependencies. Install Jetbase with the Snowflake extra:

```bash
pip install "jetbase[snowflake]"
```

### Connection String Format

```python
sqlalchemy_url = "snowflake://username:password@account/database/schema?warehouse=WAREHOUSE_NAME"
```

| Component | Description |
|-----------|-------------|
| `username` | Your Snowflake username |
| `password` | Your Snowflake password (omit for key pair auth) |
| `account` | Your Snowflake account identifier (e.g., `abc12345.us-east-1`) |
| `database` | Target database name |
| `schema` | Target schema name |
| `warehouse` | Compute warehouse to use |

### Username & Password Authentication

The simplest way to connect is with username and password:

```python
# jetbase/env.py
sqlalchemy_url = "snowflake://myuser:mypassword@myaccount.us-east-1/my_db/public?warehouse=COMPUTE_WH"
```

### Key Pair Authentication

For enhanced security, Snowflake supports key pair authentication. To use it, omit the password from your connection string and configure your private key.

**Step 1:** Create a connection string without a password:

```python
# jetbase/env.py
sqlalchemy_url = "snowflake://myuser@myaccount.us-east-1/my_db/public?warehouse=COMPUTE_WH"
```

**Step 2:** Configure your private key as an environment variable:

```bash
# Set the private key (PEM format)
export JETBASE_SNOWFLAKE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
-----END PRIVATE KEY-----"

# Optional: if your private key is encrypted
export JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD="your-key-password"
```

!!! tip
    It's best to read your private key file directly into the environment variable locally:

    ```bash
    export JETBASE_SNOWFLAKE_PRIVATE_KEY=$(cat snowflake_private_key.pem)
    ```

---

## SQLite

### Connection String

SQLite doesn't require any additional drivers. Just connect with the connection string.

```python
sqlalchemy_url = "sqlite:///path/to/database.db"
```

### Examples

**Relative path** (relative to where you run Jetbase):

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///myapp.db"
```

**In-memory database** (useful for testing):

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///:memory:"
```

**Async mode**:

```python
# jetbase/env.py
sqlalchemy_url = "sqlite+aiosqlite:///myapp.db"
```

Run with async mode:

```bash
ASYNC=true jetbase migrate
```

---

## MySQL

### Installing a Driver

MySQL requires the PyMySQL driver:

```bash
pip install pymysql
```

### Connection String

```python
sqlalchemy_url = "mysql+pymysql://username:password@host:port/database"
```

### Example

```python
# jetbase/env.py
sqlalchemy_url = "mysql+pymysql://myuser:mypassword@localhost:3306/myapp"
```

---

## Databricks

### Installing the Driver

Databricks requires additional dependencies. Install Jetbase with the Databricks extra:

```bash
pip install "jetbase[databricks]"
```

### Connection String Format

```python
sqlalchemy_url = "databricks://token:ACCESS_TOKEN@HOSTNAME?http_path=HTTP_PATH&catalog=CATALOG&schema=SCHEMA"
```

| Component | Description |
|-----------|-------------|
| `ACCESS_TOKEN` | Your Databricks personal access token |
| `HOSTNAME` | Your Databricks workspace hostname (e.g., `adb-1234567890123456.cloud.databricks.com`) |
| `HTTP_PATH` | The HTTP path to your SQL warehouse or cluster (e.g., `/sql/1.0/warehouses/abc`) |
| `CATALOG` | The Unity Catalog name to use |
| `SCHEMA` | The schema name within the catalog |

### Example

```python
# jetbase/env.py
sqlalchemy_url = "databricks://token:dapi1234567890abcdef@adb-1234567890123456.cloud.databricks.comt?http_path=/sql/1.0/warehouses/abc123def456&catalog=main&schema=default"
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASYNC` | Enable async mode (`true`/`false`) | `false` |
| `JETBASE_SQLALCHEMY_URL` | Database connection URL | Required |
| `JETBASE_POSTGRES_SCHEMA` | PostgreSQL schema search path | `public` |
| `JETBASE_SNOWFLAKE_PRIVATE_KEY` | Snowflake private key (PEM format) | Optional |
| `JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD` | Snowflake private key password | Optional |

### Connection String

```python
sqlalchemy_url = "postgresql+driver://username:password@host:port/database"
```

### Example

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+psycopg2://myuser:mypassword@localhost:5432/myapp"
```

With a specific schema:

```python
# jetbase/env.py
sqlalchemy_url = "postgresql://myuser:mypassword@localhost:5432/myapp"
postgres_schema = "public"
```

---

## Snowflake

Snowflake is a cloud-based data warehouse. Jetbase supports both username/password and key pair authentication.

### Installing the Driver

Snowflake requires additional dependencies. Install Jetbase with the Snowflake extra:

```bash
pip install "jetbase[snowflake]"
```

### Connection String Format

```python
sqlalchemy_url = "snowflake://username:password@account/database/schema?warehouse=WAREHOUSE_NAME"
```

| Component | Description |
|-----------|-------------|
| `username` | Your Snowflake username |
| `password` | Your Snowflake password (omit for key pair auth) |
| `account` | Your Snowflake account identifier (e.g., `abc12345.us-east-1`) |
| `database` | Target database name |
| `schema` | Target schema name |
| `warehouse` | Compute warehouse to use |

### Username & Password Authentication

The simplest way to connect is with username and password:

```python
# jetbase/env.py
sqlalchemy_url = "snowflake://myuser:mypassword@myaccount.us-east-1/my_db/public?warehouse=COMPUTE_WH"
```

### Key Pair Authentication

For enhanced security, Snowflake supports key pair authentication. To use it, omit the password from your connection string and configure your private key.

**Step 1:** Create a connection string without a password:

```python
# jetbase/env.py
sqlalchemy_url = "snowflake://myuser@myaccount.us-east-1/my_db/public?warehouse=COMPUTE_WH"
```

**Step 2:** Configure your private key as an environment variable:

```bash
# Set the private key (PEM format)
export JETBASE_SNOWFLAKE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
-----END PRIVATE KEY-----"

# Optional: if your private key is encrypted
export JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD="your-key-password"
```

!!! tip
    It's best to read your private key file directly into the environment variable locally:

    ```bash
    export JETBASE_SNOWFLAKE_PRIVATE_KEY=$(cat snowflake_private_key.pem)
    ```

---

## SQLite

### Connection String

SQLite doesn't require any additional drivers. Just connect with the connection string.

```python
sqlalchemy_url = "sqlite:///path/to/database.db"
```

### Examples

**Relative path** (relative to where you run Jetbase):

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///myapp.db"
```

**In-memory database** (useful for testing):

```python
# jetbase/env.py
sqlalchemy_url = "sqlite:///:memory:"
```

---


## MySQL

### Installing a Driver

MySQL requires the PyMySQL driver:

```bash
pip install pymysql
```

### Connection String

```python
sqlalchemy_url = "mysql+pymysql://username:password@host:port/database"
```

### Example

```python
# jetbase/env.py
sqlalchemy_url = "mysql+pymysql://myuser:mypassword@localhost:3306/myapp"
```

---

## Databricks

### Installing the Driver

Databricks requires additional dependencies. Install Jetbase with the Databricks extra:

```bash
pip install "jetbase[databricks]"
```

### Connection String Format

```python
sqlalchemy_url = "databricks://token:ACCESS_TOKEN@HOSTNAME?http_path=HTTP_PATH&catalog=CATALOG&schema=SCHEMA"
```

| Component | Description |
|-----------|-------------|
| `ACCESS_TOKEN` | Your Databricks personal access token |
| `HOSTNAME` | Your Databricks workspace hostname (e.g., `adb-1234567890123456.cloud.databricks.com`) |
| `HTTP_PATH` | The HTTP path to your SQL warehouse or cluster (e.g., `/sql/1.0/warehouses/abc`) |
| `CATALOG` | The Unity Catalog name to use |
| `SCHEMA` | The schema name within the catalog |


### Example

```python
# jetbase/env.py
sqlalchemy_url = "databricks://token:dapi1234567890abcdef@adb-1234567890123456.cloud.databricks.comt?http_path=/sql/1.0/warehouses/abc123def456&catalog=main&schema=default"
```
