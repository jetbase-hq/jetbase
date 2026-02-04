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

### How It Works

The `make-migrations` command:

1. **Discovers models** - Finds SQLAlchemy models from configured paths or auto-discovery
2. **Introspects database** - Reads your current database schema
3. **Compares schemas** - Identifies differences between models and database
4. **Generates SQL** - Creates upgrade and rollback statements
5. **Writes migration file** - Saves the migration to `jetbase/migrations/`

### Create SQLAlchemy Models

First, create your SQLAlchemy models with declarative base classes:

```python
# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100), nullable=True)


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

### Configure Model Paths

Jetbase supports multiple ways to specify model paths:

**Option 1: Auto-discovery (Recommended)**
Jetbase automatically finds models in `models/` or `model/` directories:

```
your-project/
├── models/
│   ├── user.py
│   ├── post.py
│   └── __init__.py
└── jetbase/
```

**Option 2: Environment Variable**
```bash
export JETBASE_MODELS="./models/user.py,./models/post.py"
```

**Option 3: Configure in env.py**
```python
# jetbase/env.py
model_paths = ["./models/user.py", "./models/post.py"]
```

### Generate Migrations

Run the make-migrations command:

```bash
# With custom description
jetbase make-migrations --description "add user profile"

# With default description
jetbase make-migrations
```

Jetbase will:
1. Compare your models against the current database schema
2. Generate a migration file if there are changes
3. Save it to `jetbase/migrations/`

Example generated migration:

```sql
-- upgrade

CREATE TABLE profiles (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bio VARCHAR(500),
    active BOOLEAN,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX ix_profiles_user_id ON profiles (user_id);


-- rollback

DROP INDEX ix_profiles_user_id ON profiles;

DROP TABLE profiles;
```

### Apply the Generated Migration

```bash
# Using the migrate command (alias for upgrade)
jetbase migrate

# Or use the traditional upgrade command
jetbase upgrade
```

### Supported Operations

The auto-generation feature detects:

| Operation | Upgrade SQL | Rollback SQL |
|-----------|-------------|--------------|
| New table | `CREATE TABLE` | `DROP TABLE` |
| New column | `ALTER TABLE ADD COLUMN` | `ALTER TABLE DROP COLUMN` |
| New index | `CREATE INDEX` / `CREATE UNIQUE INDEX` | `DROP INDEX` |
| New foreign key | `ALTER TABLE ADD CONSTRAINT` | `ALTER TABLE DROP CONSTRAINT` |

### Complete Example

```python
# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
```

Run migration generation:

```bash
$ jetbase make-migrations --description "add blogging schema"
Created migration file: V20260204_120000__add_blogging_schema.sql
```

Generated SQL:

```sql
-- upgrade

CREATE TABLE categories (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL
);

CREATE UNIQUE INDEX uniq_categories_slug ON categories (slug);

CREATE TABLE articles (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    content TEXT,
    is_published BOOLEAN,
    category_id INTEGER NOT NULL,
    CONSTRAINT fk_article_category FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE INDEX ix_articles_category_id ON articles (category_id);


-- rollback

DROP INDEX ix_articles_category_id ON articles;

DROP TABLE articles;

DROP UNIQUE INDEX uniq_categories_slug ON categories;

DROP TABLE categories;
```

Apply it:

```bash
jetbase upgrade
```

### Detecting Schema Changes

Jetbase compares your models against the **actual database** to detect:

- **New tables** not yet in the database
- **New columns** added to existing tables
- **Removed tables** that exist in DB but not in models
- **Removed columns** that exist in DB but not in models
- **New indexes** defined in models
- **New foreign keys** defined in models

### Rollback Support

Every auto-generated migration includes proper rollback SQL:

- Tables → `DROP TABLE`
- Columns → `DROP COLUMN`
- Indexes → `DROP INDEX`
- Foreign Keys → `DROP CONSTRAINT`

---

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

---

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

### make-migrations Command Options

```bash
jetbase make-migrations [OPTIONS]

Options:
  -d, --description TEXT  Description for the migration (default: "auto_generated")
  --help                 Show this message and exit
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ASYNC` | Enable async mode (`true`/`false`) |
| `JETBASE_SQLALCHEMY_URL` | Database connection URL |
| `JETBASE_MODELS` | Paths to SQLAlchemy model files |
| `JETBASE_POSTGRES_SCHEMA` | PostgreSQL schema search path |

## Need Help?

Open an issue on GitHub!
