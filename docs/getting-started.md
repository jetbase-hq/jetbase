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

Open `env.py` and update the `sqlalchemy_url` with your database connection string:

=== "PostgreSQL"
    ```python
    sqlalchemy_url = "postgresql+psycopg2://user:password@localhost:5432/mydb"
    ```

=== "SQLite"
    ```python
    sqlalchemy_url = "sqlite:///mydb.db"
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



## Creating Your First Migration

### Step 1: Generate a Migration File

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

### Step 2: Write Your Migration SQL

Open the newly created file and add your SQL statements:

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


### Step 3: Apply the Migration

Run the upgrade command:

```bash
jetbase upgrade
```

Output:

```
Migration applied successfully: V1__create_users_table.sql
```

> **Note:**  
Jetbase uses SQLAlchemy under the hood to manage database connections.  
For any database other than SQLite, you must install the appropriate Python database driver.  
For example, to use Jetbase with PostgreSQL:
```
pip install psycopg2
```
You can also use another compatible driver if you prefer (such as `asyncpg`, `pg8000`, etc.).

### Step 4: Verify the Migration

Check the migration status:

```bash
jetbase status
```

You'll see a table showing:

- ✅ Applied migrations
- 📋 Pending migrations (if any)

## What's Next?

Now that you've set up your first migration, explore these topics:

- [Writing Migrations](migrations/writing-migrations.md) — Learn about migration file syntax and best practices
- [Commands Reference](commands/index.md) — Discover all available commands
- [Rollbacks](commands/rollback.md) — Learn how to safely undo migrations
- [Configuration Options](configuration.md) — Customize Jetbase behavior

## Quick Command Reference

| Command                                                 | Description                             |
| ------------------------------------------------------- | --------------------------------------- |
| [`init`](commands/init.md)                              | Initialize Jetbase in current directory |
| [`new`](commands/new.md)                                | Create a new migration file             |
| [`upgrade`](commands/upgrade.md)                        | Apply pending migrations                |
| [`rollback`](commands/rollback.md)                      | Undo migrations                         |
| [`status`](commands/status.md)                          | Show migration status of all migration files (applied vs. pending) |
| [`history`](commands/history.md)                        | Show migration history                  |
| [`current`](commands/current.md)                        | Show latest version migrated            |
| [`lock-status`](commands/lock-status.md)                | Check if migrations are locked          |
| [`unlock`](commands/unlock.md)                          | Remove migration lock                   |
| [`validate-checksums`](commands/validate-checksums.md)  | Verify migration file integrity         |
| [`validate-files`](commands/validate-files.md)          | Check for missing migration files       |
| [`fix`](commands/fix.md)                                | Fix migration issues                    |
| [`fix-files`](commands/validate-files.md)               | Fix missing migration files (same as `validate-files --fix`) |
| [`fix-checksums`](commands/validate-checksums.md)       | Fix migration file checksums (same as `validate-checksums --fix`) |

