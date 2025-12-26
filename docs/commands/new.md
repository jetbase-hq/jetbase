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
V{YYYYMMDD.HHMMSS}__{description}.sql
```

For example:

```
V20251225.143022__create_users_table.sql
```

- `V` — Indicates a versioned migration
- `20251225.143022` — Timestamp (year, month, day, hour, minute, second)
- `create_users_table` — Your description (spaces replaced with underscores)
- `.sql` — File extension

## Examples

### Basic Usage

```bash
jetbase new "create users table"
```

Output:

```
Created migration file: /path/to/jetbase/migrations/V20251225.143022__create_users_table.sql
```

### More Examples

```bash
# Creating tables
jetbase new "create orders table"
jetbase new "create products table"

# Adding columns
jetbase new "add email to users"
jetbase new "add status column to orders"

# Creating indexes
jetbase new "add index on users email"

# Complex operations
jetbase new "add foreign key orders to users"
```

## The Generated File

The command creates an empty SQL file. You'll need to add your migration SQL:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rollback
DROP TABLE IF EXISTS users;
```

!!! tip "Best Practice"
Always include both `-- upgrade` and `-- rollback` sections. This allows you to safely undo migrations if needed.

## Tips for Good Descriptions

✅ **Good descriptions:**

```bash
jetbase new "create users table"
jetbase new "add email column to customers"
jetbase new "create index on orders date"
jetbase new "drop legacy sessions table"
```

❌ **Avoid vague descriptions:**

```bash
jetbase new "update"
jetbase new "fix"
jetbase new "changes"
```

## Notes

- Must be run from inside the `jetbase/` directory
- The file is created empty — you need to add your SQL
- Timestamp ensures migrations are always in chronological order
- Spaces in the description are automatically converted to underscores

## See Also

- [Writing Migrations](../migrations/writing-migrations.md) — Learn how to write migration files
- [`upgrade`](upgrade.md) — Apply your new migration
- [`status`](status.md) — See pending migrations
