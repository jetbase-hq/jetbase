# Migration Types 🔄

Jetbase supports three types of migrations, each suited for different use cases.

## Overview

| Type                 | Prefix  | Runs When         | Use Case                        |
| -------------------- | ------- | ----------------- | ------------------------------- |
| Versioned            | `V`     | Once, in order    | Schema changes, data migrations |
| Repeatable Always    | `RA__`  | Every upgrade     | Refreshing views, permissions   |
| Repeatable On Change | `ROC__` | When file changes | Stored procedures, functions    |

## Versioned Migrations (`V`)

The most common type. These run once, in sequential order, and are tracked by version number.

### Filename Format

```
V{YYYYMMDD.HHMMSS}__{description}.sql
```

### Examples

```
V20251225.100000__create_users_table.sql
V20251225.110000__add_email_to_users.sql
V20251225.120000__create_orders_table.sql
```

### When to Use

- Creating or altering tables
- Adding or removing columns
- Creating indexes
- Data migrations
- Any change that should only run once

### Example File

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rollback
DROP TABLE IF EXISTS users;
```

### How They Work

1. Jetbase reads all `V*` files and sorts them by version
2. Compares with applied migrations in the database
3. Applies pending migrations in order
4. Records each migration after successful execution

---

## Repeatable Always (`RA__`)

These migrations run on **every** upgrade, regardless of whether they've changed.

### Filename Format

```
RA__{description}.sql
```

### Examples

```
RA__refresh_materialized_views.sql
RA__update_permissions.sql
RA__rebuild_indexes.sql
```

### When to Use

- Refreshing materialized views
- Rebuilding indexes
- Resetting permissions or roles
- Any operation that needs to run every time

### Example File

```sql
-- upgrade
REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY order_summary;

-- Grant permissions
GRANT SELECT ON user_statistics TO readonly_role;
GRANT SELECT ON order_summary TO readonly_role;

-- rollback
-- Usually no rollback needed for RA migrations
```

### How They Work

1. After versioned migrations complete
2. Jetbase runs all `RA__*` files
3. Every `RA__` file runs on every upgrade

!!! tip
Keep `RA__` migrations idempotent (safe to run multiple times).

---

## Repeatable On Change (`ROC__`)

These migrations run only when the file content has changed since the last run.

### Filename Format

```
ROC__{description}.sql
```

### Examples

```
ROC__stored_procedures.sql
ROC__functions.sql
ROC__triggers.sql
ROC__views.sql
```

### When to Use

- Stored procedures
- Database functions
- Triggers
- Views (non-materialized)
- Any code that can be safely re-created

### Example File

```sql
-- upgrade
CREATE OR REPLACE FUNCTION calculate_order_total(order_id INTEGER)
RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT SUM(price * quantity)
        FROM order_items
        WHERE order_items.order_id = $1
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- rollback
DROP FUNCTION IF EXISTS update_timestamp();
DROP FUNCTION IF EXISTS calculate_order_total(INTEGER);
```

### How They Work

1. Jetbase calculates a checksum of the file
2. Compares with the stored checksum from last run
3. If different (or never run), executes the migration
4. Updates the stored checksum

### Why Use ROC Over V?

For functions and procedures, you often want to:

- **Edit the same file** as the function evolves
- **Avoid creating many versioned migrations** for small changes
- **Keep related code together** in one file

Compare:

**With Versioned Migrations:**

```
V20251225.100000__create_calc_total_function.sql
V20251226.100000__update_calc_total_v2.sql
V20251227.100000__update_calc_total_v3.sql
V20251228.100000__fix_calc_total_bug.sql
```

**With Repeatable On Change:**

```
ROC__order_functions.sql  # Just edit this file
```

---

## Execution Order

When you run `jetbase upgrade`, migrations execute in this order:

1. **Versioned migrations** — In version order (oldest first)
2. **Repeatable On Change** — Files that have changed
3. **Repeatable Always** — All RA files

```
[Upgrade Start]
    │
    ├── V20251225.100000__create_users.sql
    ├── V20251225.110000__create_orders.sql
    ├── V20251225.120000__add_index.sql
    │
    ├── ROC__stored_procedures.sql (if changed)
    ├── ROC__functions.sql (if changed)
    │
    ├── RA__refresh_views.sql
    └── RA__update_permissions.sql
    │
[Upgrade Complete]
```

---

## Choosing the Right Type

### Use Versioned (`V`) When:

- Making schema changes (CREATE, ALTER, DROP)
- Migrating data between tables
- Changes that must run exactly once
- Order of execution matters

### Use Repeatable Always (`RA__`) When:

- Operations need to run every deployment
- Refreshing cached/computed data
- Setting up permissions after schema changes
- Maintenance tasks

### Use Repeatable On Change (`ROC__`) When:

- Managing stored procedures/functions
- Creating views
- Setting up triggers
- Code that evolves but can be replaced

---

## File Organization

Suggested structure for your migrations folder:

```
migrations/
├── V20251220.100000__create_users.sql
├── V20251221.100000__create_orders.sql
├── V20251222.100000__add_indexes.sql
├── V20251223.100000__create_products.sql
├── ROC__order_functions.sql
├── ROC__user_functions.sql
├── ROC__triggers.sql
├── RA__refresh_views.sql
└── RA__permissions.sql
```

## See Also

- [Writing Migrations](writing-migrations.md) — Syntax and best practices
- [`upgrade` Command](../commands/upgrade.md) — Running migrations
- [`status` Command](../commands/status.md) — Viewing migration status
