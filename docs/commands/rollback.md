# jetbase rollback

Undo one or more migrations.

## Usage

```bash
jetbase rollback [OPTIONS]
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
Rollback applied successfully: V20251225.150000__add_email_to_users.sql
```

### Roll Back Multiple Migrations

```bash
# Roll back the last 3 migrations
jetbase rollback --count 3
jetbase rollback -c 3
```

Output:

```
Rollback applied successfully: V20251225.150000__add_email_to_users.sql
Rollback applied successfully: V20251225.144500__add_index_on_users.sql
Rollback applied successfully: V20251225.143022__create_users_table.sql
```

### Roll Back to a Specific Version

```bash
# Roll back everything after version 20251225.143022
jetbase rollback --to-version 20251225.143022
jetbase rollback -t 20251225_143022
```

!!! note
The specified version will **remain applied**. Only migrations after it are rolled back.

### Preview a Rollback (Dry Run)

```bash
jetbase rollback --dry-run
jetbase rollback -d
```

Output:

```
=== DRY RUN MODE ===
The following migrations would be rolled back:

--- V20251225.150000__add_email_to_users.sql ---
ALTER TABLE users DROP COLUMN email;

=== END DRY RUN ===
```

### Combine Options

```bash
# Dry-run rolling back 2 migrations
jetbase rollback --count 2 --dry-run
```

## How Rollback Works

1. **Identifies migrations to roll back** — Based on count or target version
2. **Finds the migration files** — Locates the corresponding SQL files
3. **Acquires a lock** — Prevents concurrent operations
4. **Executes rollback SQL** — Runs the `-- rollback` section of each file
5. **Updates the database** — Removes the migration record
6. **Releases the lock**

## Important Considerations

### Migration Files Must Exist

Rollback requires the original migration files to be present. If a file is missing:

```
Migration file for version '20251225.143022' not found. Cannot proceed with rollback.
Please restore the missing migration file and try again, or run 'jetbase fix'
to synchronize the migrations table with existing files before retrying the rollback.
```

**Solutions:**

1. Restore the missing file from version control
2. Run `jetbase fix` to clean up orphaned records

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

!!! warning "Destructive Operations"
Rollback operations like `DROP TABLE` are destructive. Make sure you have backups before rolling back in production!

## Common Use Cases

### Fix a Mistake in Development

```bash
# Oops, made a typo in the last migration
jetbase rollback

# Fix the SQL file, then re-apply
jetbase upgrade
```

### Revert a Feature Branch

```bash
# Roll back all migrations from your feature branch
jetbase rollback --to-version 20251220.100000
```

### Testing Migrations

```bash
# Apply migration
jetbase upgrade --count 1

# Test your application

# Roll back if there are issues
jetbase rollback

# Or continue with the rest
jetbase upgrade
```

## Error Handling

If a rollback fails:

- The failed migration remains in the database
- An error message shows what went wrong
- Fix the issue and retry

```bash
# Check current state
jetbase status

# View history to see what's applied
jetbase history
```

## Limitations

- Cannot roll back beyond the first migration
- Requires migration files to be present
- Cannot use both `--count` and `--to-version` together

## Notes

- Must be run from inside the `jetbase/` directory
- Rollbacks are applied in reverse chronological order
- Always test rollbacks in development before relying on them in production

## See Also

- [`upgrade`](upgrade.md) — Apply migrations
- [`status`](status.md) — Check current state
- [`history`](history.md) — View migration history
- [Writing Migrations](../migrations/writing-migrations.md) — Write effective rollback SQL
