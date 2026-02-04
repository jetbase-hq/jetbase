# Getting Started 🚀

This guide will walk you through setting up Jetbase from scratch. By the end, you'll have a fully working migration system for your database!

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10+** installed
- A **database** (PostgreSQL, SQLite, Snowflake, MySQL, Databricks)
- **pip** or **uv** for installing packages

## Installation

Install Jetbase using pip:

```bash
pip install jetbase
```

> **Note for Snowflake and Databricks Users:**  
> To use Jetbase with Snowflake or Databricks, install the appropriate extras:
>
> ```shell
> pip install "jetbase[snowflake]"
> pip install "jetbase[databricks]"
> ```

Verify the installation:

```bash
jetbase --help
```

You should see a list of available commands. 🎉

## Setting Up Your Project

### Step 1: Initialize Jetbase

Navigate to your project directory and run:

```bash
jetbase init
```

This creates a `jetbase/` directory with the following structure:

```
jetbase/
├── migrations/     # Your SQL migration files go here
└── env.py          # Database configuration
```

### Step 2: Navigate to the Jetbase Directory

```bash
cd jetbase
```

!!! important
All Jetbase commands must be run from inside the `jetbase/` directory.

### Step 3: Configure Your Database Connection

Open `env.py` and configure your database connection. Jetbase supports two patterns:

#### Pattern 1: Simple Module-level Variables

=== "PostgreSQL"
    ```python
    sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
    ```

=== "SQLite"
    ```python
    sqlalchemy_url = "sqlite:///mydb.db"
    ```

=== "SQLite Async"
    ```python
    sqlalchemy_url = "sqlite+aiosqlite:///mydb.db"
    async_mode = True
    ```

=== "MySQL"
    ```python
    sqlalchemy_url = "mysql+pymysql://user:password@localhost:3306/mydb"
    ```

=== "Snowflake"
    ```python
    sqlalchemy_url = (
        "snowflake://<USER>:<PASSWORD>@<ACCOUNT>/<DATABASE>/<SCHEMA>?warehouse=<WAREHOUSE>"
    )
    ```

=== "Databricks"
    ```python
    sqlalchemy_url = (
        "databricks://token:<ACCESS_TOKEN>@<HOSTNAME>?http_path=<HTTP_PATH>&catalog=<CATALOG>&schema=<SCHEMA>"
    )
    ```

#### Pattern 2: get_env_vars() Function (Recommended)

For complex configurations (environment-based settings, etc.), use a function:

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

!!! tip "Why use get_env_vars()?"
    - Keep all configuration logic in one place
    - Access to full Python logic (if/else, imports, etc.)
    - Easy to see all Jetbase configuration at a glance



## Creating Your First Migration

Jetbase offers two ways to create migrations:

### Option 1: Manual Migration (Write SQL Yourself)

Use the `new` command to create a migration file:

```bash
jetbase new "create users table" -v 1
```

This creates a file like:

```
migrations/V1__create_users_table.sql
```

The filename format is: `V{version}__{description}.sql`

!!! tip "Manual Migration Files"
    You can also create migration files manually if you prefer! Simply add your migration file to the `jetbase/migrations/` folder and follow the required filename format:  
    `V{version}__{description}.sql`  
    **Example:**  
    `V2.4__create_users_table.sql`

    Be sure your file starts with `V`, followed by a version (like `2.4`), then `__`, a short description (use underscores for spaces), and ends with `.sql`.

Write your migration SQL:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
);

-- rollback
DROP TABLE items;
DROP TABLE users;
```

!!! note "Migration File Structure"
    - The `-- rollback` section contains *only* SQL to undo the migration, and any rollback statements must go **after** `-- rollback`

### Option 2: Auto-Generate from SQLAlchemy Models

Jetbase can automatically generate SQL migrations from your SQLAlchemy models.

**Step 1:** Create your models:

```python
# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(100))


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

**Step 2:** Configure model paths in `jetbase/env.py`:

```python
model_paths = ["../models.py"]
```

Or use auto-discovery by placing models in `models/` directory.

**Step 3:** Generate migrations:

```bash
jetbase make-migrations --description "add user and post models"
```

Jetbase will:
1. Discover your models
2. Introspect the database
3. Compare schemas
4. Generate SQL with upgrade and rollback

[Learn more about auto-generation](commands/make-migrations.md)

## Apply the Migration

Run the migrate command:

```bash
jetbase migrate
```

Output:

```
Migration applied successfully: V1__create_users_table.sql
```

> **Note:**
> Jetbase uses SQLAlchemy under the hood to manage database connections.
> For any database other than SQLite, you must install the appropriate Python database driver.
> For example, to use Jetbase with PostgreSQL:
> ```
> pip install psycopg2
> ```
> You can also use another compatible driver if you prefer (such as `asyncpg`, `pg8000`, etc.).

## Verify the Migration

Check the migration status:

```bash
jetbase status
```

You'll see a table showing:

- ✅ Applied migrations
- 📋 Pending migrations (if any)

## Async and Sync Support

Jetbase supports both synchronous and asynchronous database connections.

### Using async_mode in env.py

```python
sqlalchemy_url = "sqlite+aiosqlite:///mydb.db"
async_mode = True
```

### Using ASYNC Environment Variable

```bash
# Sync mode (default)
jetbase migrate

# Async mode
ASYNC=true jetbase migrate
```

!!! note
    For SQLite async support, use `sqlite+aiosqlite://` URL scheme and set `async_mode = True`

## What's Next?

Now that you've set up your first migration, explore these topics:

- [Auto-Generation from Models](commands/make-migrations.md) — Automatically generate migrations from SQLAlchemy models
- [Writing Migrations](migrations/writing-migrations.md) — Learn about migration file syntax and best practices
- [Commands Reference](commands/index.md) — Discover all available commands
- [Rollbacks](commands/rollback.md) — Learn how to safely undo migrations
- [Configuration Options](configuration.md) — Customize Jetbase behavior
- [Database Connections](database-connections.md) — Connect to different databases with async/sync support

## Quick Command Reference

| Command                                                 | Description                             |
| ------------------------------------------------------- | --------------------------------------- |
| [`init`](commands/init.md)                              | Initialize Jetbase in current directory |
| [`new`](commands/new.md)                                | Create a new manual migration file      |
| [`make-migrations`](commands/make-migrations.md)        | Auto-generate SQL from SQLAlchemy models |
| [`migrate`](commands/upgrade.md)                        | Apply pending migrations                |
| [`upgrade`](commands/upgrade.md)                        | Apply pending migrations (alias)         |
| [`rollback`](commands/rollback.md)                      | Undo migrations                         |
| [`status`](commands/status.md)                          | Show migration status                   |
| [`history`](commands/history.md)                        | Show migration history                  |
| [`current`](commands/current.md)                        | Show latest version migrated            |
| [`lock-status`](commands/lock-status.md)                | Check if migrations are locked          |
| [`unlock`](commands/unlock.md)                          | Remove migration lock                   |
| [`validate-checksums`](commands/validate-checksums.md)  | Verify migration file integrity         |
| [`validate-files`](commands/validate-files.md)          | Check for missing migration files       |
| [`fix`](commands/fix.md)                                | Fix migration issues                    |

