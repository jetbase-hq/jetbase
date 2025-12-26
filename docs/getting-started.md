# Getting Started 🚀

This guide will walk you through setting up Jetbase from scratch. By the end, you'll have a fully working migration system for your database!

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10+** installed
- A **database** (PostgreSQL or SQLite)
- **pip** for installing packages

## Installation

Install Jetbase using pip:

```bash
pip install jetbase
```

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
    sqlalchemy_url = "postgresql://username:password@localhost:5432/database_name"
    ```

=== "SQLite"

    ```python
    sqlalchemy_url = "sqlite:///path/to/your/database.db"
    ```

!!! tip "Connection String Format" - **PostgreSQL**: `postgresql://user:password@host:port/database` - **SQLite**: `sqlite:///relative/path.db` or `sqlite:////absolute/path.db`

## Creating Your First Migration

### Step 1: Generate a Migration File

Use the `new` command to create a migration file:

```bash
jetbase new "create users table"
```

This creates a file like:

```
migrations/V20251225.143022__create_users_table.sql
```

The filename format is: `V{timestamp}__{description}.sql`

### Step 2: Write Your Migration SQL

Open the newly created file and add your SQL statements:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rollback
DROP TABLE IF EXISTS users;
```

!!! note "Migration File Structure" - The `-- upgrade` section contains SQL to apply the migration - The `-- rollback` section contains SQL to undo the migration - Always include both sections for safe rollbacks!

### Step 3: Apply the Migration

Run the upgrade command:

```bash
jetbase upgrade
```

Output:

```
Migration applied successfully: V20251225.143022__create_users_table.sql
```

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

| Command                     | Description                             |
| --------------------------- | --------------------------------------- |
| `jetbase init`              | Initialize Jetbase in current directory |
| `jetbase new "description"` | Create a new migration file             |
| `jetbase upgrade`           | Apply pending migrations                |
| `jetbase rollback`          | Undo the last migration                 |
| `jetbase status`            | Show migration status                   |
| `jetbase history`           | Show migration history                  |
| `jetbase current`           | Show current migration version          |

## Troubleshooting

### "Jetbase directory not found"

Make sure you're running commands from inside the `jetbase/` directory, not your project root.

### "Connection refused"

Double-check your database connection string in `env.py`. Make sure your database server is running.

### "Permission denied"

Ensure your database user has the necessary permissions to create tables and execute DDL statements.

---

Need more help? Check out the [Troubleshooting Guide](troubleshooting.md) or open an issue on GitHub!
