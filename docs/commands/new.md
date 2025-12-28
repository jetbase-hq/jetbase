# jetbase new

Create a new migration file with a timestamped version.

## Usage

```bash
jetbase new "description of the migration"
```

## Description

The `new` command generates a new SQL migration file in the `migrations/` directory. The file is automatically named with a timestamp-based version number, ensuring migrations are applied in the correct order.

## Arguments

| Argument      | Required | Description                                    |
| ------------- | -------- | ---------------------------------------------- |
| `description` | Yes      | A brief description of what the migration does |

## Filename Format

The generated filename follows this pattern:

```
V<YYYYMMDD.HHMMSS>__<description>.sql
```

For example:

```
V20251225.143022__create_users_table.sql
```

- `V` — Indicates a versioned migration
- `20251225.143022` — Timestamp (year, month, day, hour, minute, second)
- `create_users_table` — Your description (spaces replaced with underscores)
- `.sql` — File extension

!!! tip "Manual Migration Files"
You don't *have* to use the `jetbase new` CLI command to add a migration!  
You can manually create a migration file in the required format:

```
V<version>__<description>.sql
```

**Examples:**
- `V1__create_users_table.sql`
- `V1.1__create_users_table.sql`

Just ensure your filename starts with `V`, followed by a version (or timestamp), double underscore `__`, a short description (use underscores for spaces), and ends with `.sql`.

## Examples

### Basic Usage

```bash
jetbase new "create users table"
```

Output:

```
Created migration file: /path/to/jetbase/migrations/V20251225.143022__create_users_table.sql
```


## The Generated File

The command creates an empty SQL file. You'll need to add your migration SQL:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- rollback
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS items;
```

!!! tip "Best Practice"
Include `-- rollback` sections. This allows you to safely undo migrations if needed.


## Notes

- Must be run from inside the `jetbase/` directory
- The file is created empty — you need to add your SQL
- Timestamp ensures migrations are always in chronological order
- Spaces in the description are automatically converted to underscores

## See Also

- [Writing Migrations](../migrations/writing-migrations.md) — Learn how to write migration files
- [`upgrade`](upgrade.md) — Apply your new migration
- [`status`](status.md) — See pending migrations
