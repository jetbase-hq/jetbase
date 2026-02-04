# Welcome to Jetbase 🚀

**Jetbase** is a simple, lightweight database migration tool for Python projects.

Jetbase helps you manage database migrations in a simple, version-controlled way. Whether you're adding a new table, modifying columns, or need to undo a change, Jetbase makes it super easy!

---

**Created and maintained by [Jaz](https://github.com/jaz-alli) 🛠️**

---


### Key Features ✨

- **📦 Simple Setup** — Get started with just one command
- **⬆️ Easy Upgrades** — Apply pending migrations with confidence
- **⬇️ Safe Rollbacks** — Made a mistake? No problem, roll it back!
- **📊 Clear Status** — Always know which migrations have been applied and which are pending
- **🔒 Migration Locking** — Prevents conflicts when multiple processes try to migrate
- **✅ Checksum Validation** — Detects if migration files have been modified
- **🔄 Repeatable Migrations** — Support for migrations that run on every upgrade
- **🤖 Auto-Generation** — Automatically generate SQL migrations from SQLAlchemy models
- **🔀 Async/Sync Support** — Works with both sync and async SQLAlchemy drivers
- **🎯 Auto-Discovery** — Automatically finds models in `models/` or `model/` directories
- **📁 Portable** — Run jetbase from any directory in your project

[📚 Full Documentation](https://jetbase-hq.github.io/jetbase/)

## Quick Start 🏃‍♂️

### Installation

**Using pip:**
```shell
pip install jetbase
```

**Using uv:**
```shell
uv add jetbase
```

> **Note for Snowflake and Databricks Users:**  
> To use Jetbase with Snowflake or Databricks, install the appropriate extras:
>
> ```shell
> pip install "jetbase[snowflake]"
> pip install "jetbase[databricks]"
> ```



### Initialize Your Project

```bash
jetbase init
```

This creates a `jetbase/` directory with:

- A `migrations/` folder for your SQL files
- An `env.py` configuration file

> **Tip:** Run `jetbase` commands from **any directory** in your project. Jetbase automatically finds the `jetbase/` directory by searching up the directory tree.

### Configure Your Database

Edit `jetbase/env.py` with your database connection string (currently support for postgres, sqlite snowflake, databricks):

**PostgreSQL example:**
```python
sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
```

**SQLite example:**
```python
sqlalchemy_url = "sqlite:///mydb.db"
```

### Create Your First Migration

```bash
jetbase new "create users table" -v 1
```

This creates a new SQL file called `V1__create_users_table.sql`.

> **Tip:**  
> You can also create migrations manually by adding SQL files in the `jetbase/migrations` directory, using the `V<version>__<description>.sql` naming convention (e.g., `V1__add_users_table.sql`, `V2.4__add_users_table.sql`).


### Write Your Migration

Open the newly created file and add your SQL:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- rollback
DROP TABLE items;
DROP TABLE users;
```

### Apply the Migration

```bash
jetbase upgrade
```

That's it! Your database is now up to date. 🎉

> **Note:**  
> Jetbase uses SQLAlchemy under the hood to manage database connections.  
> For any database other than SQLite, you must install the appropriate Python database driver.  
> For example, to use Jetbase with PostgreSQL:

```bash
pip install psycopg2
```

You can also use another compatible driver if you prefer (such as `asyncpg`, `pg8000`, etc.).

---

## Automatic Migration Generation 🤖

Jetbase can automatically generate SQL migration files from your SQLAlchemy model definitions. This feature is similar to Django's `makemigrations` command.

### Prerequisites

1. Create SQLAlchemy model files with declarative base classes:

```python
# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(100))

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    price = Column(Integer)
```

### Auto-Discovery of Models 🎯

Jetbase automatically discovers models in your project without needing to configure paths:

1. **Option 1: Auto-discovery** - Jetbase looks for models in:
   - `models/` directory
   - `model/` directory
   - Searches recursively through subdirectories

   ```
   your-project/
   ├── models/
   │   ├── user.py
   │   ├── product/
   │   │   └── __init__.py
   │   └── order.py
   └── jetbase/
   ```

2. **Option 2: Explicit configuration** - Set the `JETBASE_MODELS` environment variable:

   ```bash
   # Single model file
   export JETBASE_MODELS="./models.py"

   # Multiple model files (comma-separated)
   export JETBASE_MODELS="./models/user.py,./models/product.py,./models/order.py"
   ```

3. **Option 3: Configure in env.py** - Add model paths in your configuration:

   ```python
   # jetbase/env.py
   model_paths = ["./models/user.py", "./models/product.py"]
   ```

> **Note:** Jetbase automatically adds your project root to `sys.path` so models can use absolute imports.

### Generate Migrations Automatically

```bash
jetbase make-migrations --description "create users and products"
```

This will:
1. Read your model definitions from the paths specified in `JETBASE_MODELS`
2. Introspect your current database schema
3. Compare models against the database
4. Generate a migration file with upgrade and rollback SQL

Example generated migration:

```sql
-- upgrade

CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100)
);

CREATE TABLE products (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price INTEGER
);

-- rollback

DROP TABLE products;
DROP TABLE users;
```

### Apply the Generated Migration

```bash
# Using the new migrate command (alias for upgrade)
jetbase migrate

# Or use the traditional upgrade command
jetbase upgrade
```

### Supported Operations

The auto-generation feature detects:
- ✅ New tables to create
- ✅ Columns added/removed/modified
- ✅ Index creation/removal
- ✅ Foreign key creation/removal

### Environment Variable Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ASYNC` | Enable async mode (`true`/`false`) | `false` |
| `JETBASE_SQLALCHEMY_URL` | Database connection URL | Required |
| `JETBASE_MODELS` | Paths to SQLAlchemy models | Optional |

You can also configure model paths in `jetbase/env.py`:

```python
model_paths = ["./models/user.py", "./models/product.py"]
```

> **Note:** When `ASYNC=false` (default), Jetbase automatically strips async driver suffixes (`+asyncpg`, `+aiosqlite`, `+async`) from the URL, allowing you to use async URLs in sync mode.

## Supported Databases

Jetbase currently supports:

- ✅ PostgreSQL
- ✅ SQLite
- ✅ Snowflake
- ✅ Databricks
- ✅ MySQL

---

## Async and Sync Database Support ⚡

Jetbase supports both synchronous and asynchronous database connections. The mode is controlled **exclusively** by the `ASYNC` environment variable.

### Configuration

Set the `ASYNC` environment variable before running Jetbase commands:

```bash
export ASYNC=true   # for async mode
export ASYNC=false  # for sync mode (default)
jetbase status
```

You can also set it temporarily per command:

```bash
ASYNC=true jetbase status      # async mode
ASYNC=false jetbase upgrade    # sync mode
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

Sync mode is the default. Just run:

```bash
jetbase upgrade
```

### Async Mode

Use async drivers:

```python
# jetbase/env.py
sqlalchemy_url = "postgresql+asyncpg://user:password@localhost:5432/mydb"
# or
sqlalchemy_url = "sqlite+aiosqlite:///mydb.db"
```

Set `ASYNC=true`:

```bash
export ASYNC=true
jetbase upgrade
```

### Environment Variable Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ASYNC` | Enable async mode (`true`/`false`) | `false` |
| `JETBASE_SQLALCHEMY_URL` | Database connection URL | Required |
| `JETBASE_MODELS` | Paths to SQLAlchemy models | Optional |

### URL Format Reference

| Database | Sync URL | Async URL |
|----------|----------|-----------|
| PostgreSQL | `postgresql+psycopg2://...` | `postgresql+asyncpg://...` |
| SQLite | `sqlite:///path.db` | `sqlite+aiosqlite:///path.db` |
| Snowflake | `snowflake://...` | Not supported |
| MySQL | `mysql+pymysql://...` | Not supported |
| Databricks | `databricks+connector://...` | Not supported |

> **Note:** Only PostgreSQL and SQLite support async mode. Other databases use sync connections regardless of the `ASYNC` setting.

## Commands Reference

| Command | Description |
|---------|-------------|
| `jetbase init` | Initialize a new Jetbase project |
| `jetbase new "description"` | Create a new manual migration file |
| `jetbase make-migrations` | Auto-generate SQL from SQLAlchemy models |
| `jetbase upgrade` | Apply pending migrations |
| `jetbase migrate` | Apply migrations (alias for upgrade) |
| `jetbase rollback` | Rollback migrations |
| `jetbase status` | Show migration status |
| `jetbase history` | Show migration history |
| `jetbase current` | Show current version |
| `jetbase validate` | Validate migration files and checksums |
| `jetbase lock` | Acquire migration lock |
| `jetbase unlock` | Release migration lock |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ASYNC` | Enable async mode (`true`/`false`) |
| `JETBASE_SQLALCHEMY_URL` | Database connection URL |
| `JETBASE_MODELS` | Paths to SQLAlchemy model files |
| `JETBASE_POSTGRES_SCHEMA` | PostgreSQL schema search path |

## Need Help?

Open an issue on GitHub!
