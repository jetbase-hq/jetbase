# jetbase rollback

Undo one or more migrations.

## Usage

```bash
jetbase rollback
```

## Description

The `rollback` command undoes applied migrations by executing the `-- rollback` section of migration files. This is essential for recovering from mistakes or reverting changes during development.

## Options

| Option         | Short | Description                                 |
| -------------- | ----- | ------------------------------------------- |
| `--count`      | `-c`  | Number of migrations to roll back           |
| `--to-version` | `-t`  | Roll back to a specific version (exclusive) |
| `--dry-run`    | `-d`  | Preview the rollback without executing it   |

## Default Behavior

When called without options, `rollback` undoes **only the last migration**:

```bash
jetbase rollback
```

This is equivalent to:

```bash
jetbase rollback --count 1
```

## Examples

### Roll Back the Last Migration

```bash
jetbase rollback
```

Output:

```
Rollback applied successfully: V10__add_email_to_users.sql
```

### Rollback Multiple Migrations

```bash
# Roll back the last 3 migrations
jetbase rollback --count 3
```

Output:

```
Rollback applied successfully: V10__add_email_to_users.sql
Rollback applied successfully: V9__add_index_on_users.sql
Rollback applied successfully: V8__create_users_table.sql
```

### Roll Back to a Specific Version

```bash
# Roll back everything after version 20251225.143022
jetbase rollback --to-version 5
```

!!! note
The specified version will **remain applied**. Only migrations after it are rolled back.

### Preview a Rollback (Dry Run)

```bash
jetbase rollback --dry-run
```

Output:

```
=== DRY RUN MODE ===
The following migrations would be rolled back:

--- V10__add_email_to_users.sql ---
ALTER TABLE users DROP COLUMN email;

=== END DRY RUN ===
```

### Combine Options

```bash
# Dry-run rolling back 2 migrations
jetbase rollback --count 2 --dry-run
```

## Important Considerations

### Migration Files Must Exist

Rollback requires the original migration files to be present. If a file is missing:

```
Migration file for version '7' not found. Cannot proceed with rollback.
Please restore the missing migration file and try again, or run 'jetbase fix'
to synchronize the migrations table with existing files before retrying the rollback.
```

**Solutions:**

1. Restore the missing migration file to its correct location.
2. Alternatively, run `jetbase fix` to synchronize the migrations table with the current set of files.  
   _Note: This will remove references to the missing migration from tracking. If you need to roll back past that point in the future, you'll need to write a new migration file to handle it safely._

### Order of Rollback

Migrations are rolled back in **reverse order** (newest first). This ensures dependencies are handled correctly.

### Write Good Rollback SQL

Your rollback SQL should completely undo the upgrade:

```sql
-- upgrade
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10,2)
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- rollback
DROP INDEX IF EXISTS idx_orders_user_id;
DROP TABLE IF EXISTS orders;
```


## Error Handling

If a rollback fails:

- The failed migration remains in the database
- Fix the rollback statement directly in the migration file ( there is no checksum validation for rollback statements)
- If you are rolling back multiple migrations in a single command:
    - Any migrations that are successfully rolled back before an error will remain rolled back
    - If a failure occurs, all SQL statements for that migration’s rollback section are aborted
    - Migrations scheduled to roll back after the failed one will not be attempted


```bash
# Check current state of what migrations have been applied and what is pending
jetbase status
```


## Notes

- Must be run from inside the `jetbase/` directory
- Rollbacks are applied in reverse chronological order
- Cannot use both `--count` and `--to-version` together

