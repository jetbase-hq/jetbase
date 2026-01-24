# Database Connections 🔌

Jetbase supports multiple databases. This guide covers how to connect to each supported database using a SQLAlchemy url.

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
