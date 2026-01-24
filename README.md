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
cd jetbase
```

This creates a `jetbase/` directory with:

- A `migrations/` folder for your SQL files
- An `env.py` configuration file

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

## Supported Databases

Jetbase currently supports:

- ✅ PostgreSQL
- ✅ SQLite
- ✅ Snowflake
- ✅ Databricks
- ✅ MySQL

## Need Help?

Open an issue on GitHub!
