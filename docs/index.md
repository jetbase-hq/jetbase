# Welcome to Jetbase 🚀

**Jetbase** is a simple, lightweight database migration tool for Python projects.

Jetbase helps you manage database migrations in a simple, version-controlled way. Whether you're adding a new table, modifying columns, or need to undo a change, Jetbase makes it super easy!

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

## Quick Start 🏃‍♂️

### Installation

=== "pip"

    ```shell
    pip install jetbase
    ```

=== "uv"

    ```shell
    uv add jetbase
    ```

### Initialize Your Project

```bash
jetbase init
cd jetbase
```

This creates a `jetbase/` directory with:

- A `migrations/` folder for your SQL files
- An `env.py` configuration file

### Configure Your Database

Edit `jetbase/env.py` with your database connection string:

=== "PostgreSQL"

    ```python
    sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
    ```

=== "MySQL"

    ```python
    sqlalchemy_url = "mysql+pymysql://user:password@localhost:3306/mydb"
    ```

=== "SQLite"

    ```python
    sqlalchemy_url = "sqlite:///mydb.db"
    ```

=== "Snowflake"

    ```python
    sqlalchemy_url = "snowflake://user:password@account/database/schema?warehouse=WAREHOUSE"
    ```

### Create Your First Migration

```bash
jetbase new "create users table" -v 1
```

This creates a new SQL file called `V1__create_users_table.sql`.

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
    name VARCHAR(100) NOT NULL,
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

!!! note
    Jetbase uses SQLAlchemy under the hood to manage database connections.
    For any database other than SQLite, you must install the appropriate Python database driver.
    For example, to use Jetbase with PostgreSQL:

    ```
    pip install psycopg2
    ```

    You can also use another compatible driver if you prefer (such as `asyncpg`, `pg8000`, etc.).

## Auto-Generation from SQLAlchemy Models 🤖

Jetbase can automatically generate SQL migrations from your SQLAlchemy model definitions:

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
```

Generate migrations automatically:

```bash
jetbase make-migrations --description "add user model"
```

Jetbase will:
1. Discover your models from `models/` directory or configured paths
2. Introspect your current database schema
3. Compare models against the database
4. Generate a migration file with upgrade and rollback SQL

[Learn more about auto-generation](commands/make-migrations.md)

## Async and Sync Support ⚡

Jetbase supports both synchronous and asynchronous database connections:

```bash
# Sync mode (default)
jetbase upgrade

# Async mode
ASYNC=true jetbase upgrade
```

[Learn more about async/sync support](database-connections.md#async-and-sync-modes)

## Next Steps

- 📖 [Getting Started Guide](getting-started.md) — More detailed setup instructions
- 🛠️ [Commands Reference](commands/index.md) — Learn all available commands
- 📝 [Writing Migrations](migrations/index.md) — Best practices for migration files
- ⚙️ [Configuration](configuration.md) — Customize Jetbase for your needs
- 🔌 [Database Connections](database-connections.md) — Connect to different databases

## Supported Databases

Jetbase currently supports:

- ✅ PostgreSQL
- ✅ SQLite
- ✅ Snowflake
- ✅ MySQL
- ✅ Databricks
