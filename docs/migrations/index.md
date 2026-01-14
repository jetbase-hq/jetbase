# Migrations Overview

Learn how to write and organize database migrations with Jetbase.

## What are Migrations?

Migrations are SQL files that describe changes to your database schema. They let you:

- **Version control** your database schema alongside your code
- **Apply changes** consistently across development, staging, and production
- **Rollback** changes when something goes wrong
- **Collaborate** with your team on database changes


## Quick Start

### Create a Migration

You can create migrations in two ways:

**Option 1: Using the CLI**

```bash
jetbase new "create users table" -v 1

# if you want a timestamp-based version, do not specify a version
jetbase new "create users table"
```

This automatically generates a properly formatted migration file.

**Option 2: Creating files manually**

Create a file in your `migrations/` directory following the naming convention:

```
V<version>__<description>.sql
```

Examples: `V1__create_users_table.sql`, `V1.1__add_email_column.sql`

### Migration Version Order

Jetbase always applies migrations in version order—from lowest to highest.

Whenever you add a new migration file, make sure its version number is higher than any migration that’s already been applied.

If you accidentally create a migration with a lower version number than the last one applied, Jetbase will catch it and let you know before anything happens.

This simple check helps keep your migration history clean, safe, and easy to follow!

!!! tip "Versioning Example"
    - ✅ Good: `V1.1__create_table.sql` > `V1.2__add_column.sql`
    - ❌ Bad: `V1.2__add_column.sql` (already applied)  
      New file: `V1.1__add_last_name_column.sql` ← lower version!

If you ever need to bypass this check *(not recommended)*, you have two options:

- **Command-line:**  
  Add `--skip-file-validation` when running `jetbase upgrade`:
  ```bash
  jetbase upgrade --skip-file-validation
  ```


- **Configuration:**  
  Set `skip_file_validation = True` in your `env.py` or `pyproject.toml`.

!!! warning
    If you skip this check, Jetbase will simply *ignore* any migration file whose version is lower than the last applied migration—no error message will be shown, and that migration won't be run.

### Writing the Migration File

Writing Jetbase SQL migration files is easy! Just follow these simple guidelines:

- **Multiple Statements:** Add as many SQL statements as you need. Just make sure each one ends with a semicolon (`;`).
- **Upgrade & Rollback Sections:** Separate your *upgrade* statements from *rollback* statements by adding a line with `-- rollback`. (Any variation in case and spacing works: `--rollback`, `-- ROLLBACK`, etc.)
- **Section Rules:** Only a single upgrade section and a single rollback section are allowed. Everything above the first `-- rollback` is considered an upgrade; everything below is a rollback.

    💡 You don't have to include a `-- rollback` section (though it's highly recommended!). If you leave it out, Jetbase will treat *all* SQL statements in the file as upgrade statements.

- **Comments:** Feel free to include comments! Just start a line with `--` and Jetbase will ignore it.

That’s it!

Examples:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
);

-- rollback
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS items;
```

```sql
-- upgrade

-- my first comment
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- my second comment
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
);

-- rollback
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;
```

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- items table
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
);
```

### Apply It

```bash
jetbase upgrade
```

## Migration Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Create    │ ──▶ │    Write    │ ──▶ │   Apply     │
│ jetbase new │     │    SQL      │     │  upgrade    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Rollback  │ ◀── │   Oops?     │
                    │  if needed  │     │             │
                    └─────────────┘     └─────────────┘
```

## File Naming

| Type                 | Pattern                    | Example                              |
| -------------------- | -------------------------- | ------------------------------------ |
| Versioned            | `V{version}__{desc}.sql` | `V1__create_users.sql` |
| Runs Always          | `RA__{desc}.sql`           | `RA__refresh_views.sql`              |
| Runs On Change       | `ROC__{desc}.sql`          | `ROC__functions.sql`                 |

## Best Practices

1. **One change per migration** — Keep migrations focused
2. **Include rollback** — Even if it's just `DROP TABLE`
3. **Use descriptive names** — Future you will thank you
4. **Test locally first** — Use dry-run before production
5. **Don't modify applied migrations** — Create new ones instead

## In-File Configuration

### Custom Delimiter

By default, Jetbase splits SQL statements on semicolons (`;`). However, when working with stored procedures, functions, or triggers that contain semicolons in their body, you may need a custom delimiter.

Add a special comment at the top of your migration file to specify a custom delimiter:


```sql
-- jetbase: delimiter=<delimiter>
```

**In this example below, the delimiter to split SQL statements on in the file will be ~**
```sql
-- jetbase: delimiter=~
```

In this example, the delimiter to split SQL statements on in the file will be ~

**Example file:**

```sql
-- jetbase: delimiter=~

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    updated_at TIMESTAMP
);~

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;~

CREATE TRIGGER users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();~

-- rollback
DROP TRIGGER IF EXISTS users_updated_at ON users;~
DROP FUNCTION IF EXISTS set_updated_at();~
DROP TABLE IF EXISTS users;~
```


!!! note
    The `-- jetbase: delimiter=` directive must appear before any SQL statements (comments are okay).

