# Migrations Overview

Learn how to write and organize database migrations with Jetbase.

## What are Migrations?

Migrations are SQL files that describe changes to your database schema. They let you:

- **Version control** your database schema alongside your code
- **Apply changes** consistently across development, staging, and production
- **Roll back** changes when something goes wrong
- **Collaborate** with your team on database changes

## Guides

<div class="grid cards" markdown>

- 📝 **[Writing Migrations](writing-migrations.md)**

  ***

  Learn the syntax and best practices for writing effective migration files.

- 🔄 **[Migration Types](migration-types.md)**

  ***

  Understand versioned, repeatable always, and repeatable on change migrations.

</div>

## Quick Start

### Create a Migration

```bash
jetbase new "create users table"
```

### Write the SQL

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- rollback
DROP TABLE IF EXISTS users;
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
| Versioned            | `V{timestamp}__{desc}.sql` | `V20251225.143022__create_users.sql` |
| Repeatable Always    | `RA__{desc}.sql`           | `RA__refresh_views.sql`              |
| Repeatable On Change | `ROC__{desc}.sql`          | `ROC__functions.sql`                 |

## Best Practices

1. **One change per migration** — Keep migrations focused
2. **Always include rollback** — Even if it's just `DROP TABLE`
3. **Use descriptive names** — Future you will thank you
4. **Test locally first** — Use dry-run before production
5. **Don't modify applied migrations** — Create new ones instead
