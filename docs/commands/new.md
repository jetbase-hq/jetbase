# jetbase new

Create a new migration file with a specified version.

## Usage

```bash
jetbase new "description of the migration" -v <version>
```

## Description

The `new` command generates a new SQL migration file in the `migrations/` directory. The file is named with the provided version number and description.

If you do not provide a version, the file generated will use the current timestamp as the version.

## Arguments

| Argument      | Required | Description                                    |
| ------------- | -------- | ---------------------------------------------- |
| `description` | Yes      | A brief description of what the migration does |

## Options

| Option              | Required | Description                                                                 |
| ------------------- | -------- | --------------------------------------------------------------------------- |
| `-v`, `--version`   | No       | The version number for the migration (e.g., `1`, `1.5`, `2_1`). If not provided, a timestamp is used. |

## Filename Format

The generated filename follows this pattern:

```
# with version provided
V<version>__<description>.sql

#without version provided
V<YYYYMMDD.HHMMSS>__<description>.sql
```

For example, with `-v 1`:

```
V1__create_users_table.sql
```

Or without `-v` (uses timestamp):

```
V20251225.143022__create_users_table.sql
```

- `V` — Indicates a versioned migration
- `1` or `20251225.143022` — Version number or timestamp
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
jetbase new "create users table" -v 1
```

Output:

```
Created migration file: V1__create_users_table.sql
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
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;
```

!!! tip "Best Practice"
Include `-- rollback` sections. This allows you to safely undo migrations if needed.


## Notes

- Must be run from inside the `jetbase/` directory
- Use `-v` to specify a custom version number (e.g., `1`, `1.5`)
- If `-v` is not provided, a timestamp-based version is automatically generated
- You do not have to use the `jetbase new` CLI command to create a new migration. You can create a new file manually in the `jetbase/migrations` directory and follow the `V<version>__<description>.sql` naming convention. For full details and best practices, see [Migrations Overview](../migrations/index.md).

