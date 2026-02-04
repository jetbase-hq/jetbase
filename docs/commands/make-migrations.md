# jetbase make-migrations

Automatically generate SQL migration files from your SQLAlchemy model definitions.

## Usage

```bash
jetbase make-migrations [OPTIONS]
```

## Description

The `make-migrations` command automatically generates SQL migration files by:

1. **Discovering models** - Finds SQLAlchemy models from configured paths
2. **Introspecting database** - Reads your current database schema
3. **Comparing schemas** - Identifies differences between models and database
4. **Generating SQL** - Creates upgrade and rollback statements
5. **Writing migration file** - Saves the migration to `jetbase/migrations/`

## Options

| Option | Required | Description |
|--------|----------|-------------|
| `-d`, `--description` | No | Description for the migration (default: "auto_generated") |

## Arguments

This command has no positional arguments.

## How It Works

### Step 1: Model Discovery

Jetbase finds your SQLAlchemy models using one of these methods:

**Auto-discovery** (recommended):
```
your-project/
├── models/
│   ├── user.py
│   ├── post.py
│   └── __init__.py
└── jetbase/
```

**Explicit configuration** via `JETBASE_MODELS`:
```bash
export JETBASE_MODELS="./models/user.py,./models/post.py"
```

**Or in env.py**:
```python
# jetbase/env.py
model_paths = ["./models/user.py", "./models/post.py"]
```

### Step 2: Database Introspection

Jetbase connects to your database and reads the current schema.

### Step 3: Schema Comparison

Jetbase compares your models against the database to detect:
- New tables to create
- New columns to add
- Tables/columns to remove
- New indexes
- New foreign keys

### Step 4: SQL Generation

Jetbase generates appropriate SQL for each change.

### Step 5: File Creation

Creates a migration file in `jetbase/migrations/`.

## Prerequisites

### Create SQLAlchemy Models

Your models must use declarative base:

```python
# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

## Supported Operations

| Operation | Upgrade SQL | Rollback SQL |
|-----------|-------------|--------------|
| New table | `CREATE TABLE` | `DROP TABLE` |
| New column | `ALTER TABLE ADD COLUMN` | `ALTER TABLE DROP COLUMN` |
| New index | `CREATE INDEX` | `DROP INDEX` |
| New unique index | `CREATE UNIQUE INDEX` | `DROP INDEX` |
| New foreign key | `ALTER TABLE ADD CONSTRAINT` | `ALTER TABLE DROP CONSTRAINT` |

## Examples

### Basic Usage

```bash
jetbase make-migrations
```

Output:

```
Created migration file: V20260204.120000__auto_generated.sql
```

### With Custom Description

```bash
jetbase make-migrations --description "add user profile"
```

Output:

```
Created migration file: V20260204.120000__add_user_profile.sql
```

## Generated File Example

Input models:

```python
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
```

Generated migration:

```sql
-- upgrade

CREATE TABLE categories (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100)
);

CREATE UNIQUE INDEX uniq_categories_slug ON categories (slug);

CREATE TABLE articles (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
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

## Apply the Migration

```bash
jetbase migrate
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JETBASE_MODELS` | Comma-separated paths to SQLAlchemy model files |
| `ASYNC` | Enable async mode (`true`/`false`, default: `false`) |

### Model Path Configuration

=== "Auto-discovery (Recommended)"
    Place your models in `models/` or `model/` directory:
    ```
    your-project/
    ├── models/
    │   ├── user.py
    │   └── post.py
    └── jetbase/
    ```

=== "Environment Variable"
    ```bash
    export JETBASE_MODELS="./models/user.py,./models/post.py"
    ```

=== "env.py Configuration"
    ```python
    # jetbase/env.py
    model_paths = ["./models/user.py", "./models/post.py"]
    ```

## Async Mode

The `make-migrations` command respects the `ASYNC` environment variable:

```bash
# Sync mode (default)
jetbase make-migrations

# Async mode
ASYNC=true jetbase make-migrations
```

When `ASYNC=true`, Jetbase uses async database connections for introspection.

## Notes

- Jetbase compares models against the **actual database**, not against previous migrations
- Models must use `declarative_base()` from SQLAlchemy
- The `__tablename__` attribute is required
- Foreign keys require `ForeignKey` imports from SQLAlchemy
- Migration files are saved to `jetbase/migrations/`

## See Also

- [Writing Migrations](../migrations/writing-migrations.md)
- [Commands Reference](index.md)
- [Configuration](../configuration.md)
