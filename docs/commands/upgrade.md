# jetbase upgrade

Apply pending migrations to your database.

## Usage

```bash
jetbase upgrade [OPTIONS]
```

## Description

The `upgrade` command applies all pending migrations to your database in order. It's the most commonly used command for keeping your database schema up to date.

## Options

| Option                       | Short | Description                               |
| ---------------------------- | ----- | ----------------------------------------- |
| `--count`                    | `-c`  | Number of migrations to apply             |
| `--to-version`               | `-t`  | Apply migrations up to a specific version |
| `--dry-run`                  | `-d`  | Preview changes without applying them     |
| `--skip-validation`          |       | Skip all validation checks                |
| `--skip-checksum-validation` |       | Skip checksum validation only             |
| `--skip-file-validation`     |       | Skip file validation only                 |

## Examples

### Apply All Pending Migrations

```bash
jetbase upgrade
```

This applies all pending migrations in order.

### Apply a Specific Number of Migrations

```bash
# Apply only the next 2 migrations
jetbase upgrade --count 2
jetbase upgrade -c 2
```

### Apply Up to a Specific Version

```bash
# Apply all migrations up to and including version 20251225.150000
jetbase upgrade --to-version 20251225.150000
jetbase upgrade -t 20251225.150000
```

!!! note
Use underscores instead of dots in the version number: `20251225_150000`

### Preview Changes (Dry Run)

```bash
jetbase upgrade --dry-run
jetbase upgrade -d
```

This shows you what migrations would be applied without actually running them. Great for verifying before deployment!

Output example:

```
=== DRY RUN MODE ===
The following migrations would be applied:

--- V20251225.143022__create_users_table.sql ---
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL
);

--- V20251225.144500__add_email_to_users.sql ---
ALTER TABLE users ADD COLUMN email VARCHAR(255);

=== END DRY RUN ===
```

### Skip Validation

```bash
# Skip all validation (use with caution!)
jetbase upgrade --skip-validation

# Skip only checksum validation
jetbase upgrade --skip-checksum-validation

# Skip only file validation
jetbase upgrade --skip-file-validation
```

!!! warning
Skipping validation can lead to inconsistent database state. Only use these options if you understand the implications.

## How It Works

1. **Checks for pending migrations** — Compares files in `migrations/` with the database
2. **Validates existing migrations** — Ensures checksums and files match (unless skipped)
3. **Acquires a lock** — Prevents other processes from running migrations simultaneously
4. **Applies migrations in order** — Executes the `-- upgrade` section of each file
5. **Records the migration** — Stores version, checksum, and timestamp in the database
6. **Releases the lock** — Allows other processes to run migrations

## Migration Types

During upgrade, Jetbase processes three types of migrations:

### Versioned Migrations (`V*`)

Standard migrations that run once, in version order.

```
V20251225.143022__create_users.sql
```

### Repeatable Always (`RA__*`)

Migrations that run on every upgrade.

```
RA__refresh_views.sql
```

### Repeatable On Change (`ROC__*`)

Migrations that run only when the file content changes.

```
ROC__stored_procedures.sql
```

Learn more in [Migration Types](../migrations/migration-types.md).

## Common Use Cases

### Deploying to Production

```bash
# First, preview what will run
jetbase upgrade --dry-run

# If everything looks good, apply
jetbase upgrade
```

### Incremental Development

```bash
# Apply migrations one at a time to test
jetbase upgrade --count 1

# Check status after each one
jetbase status
```

### Rolling Back After Failed Upgrade

If an upgrade fails midway:

```bash
# Check current state
jetbase status

# Roll back to a known good state
jetbase rollback --to-version 20251225.143022
```

## Error Handling

If a migration fails:

1. The failing migration is **not recorded** in the database
2. The lock is **released**
3. You'll see an error message with details
4. Your database remains in its previous state (for that migration)

!!! tip
Always use transactions in your migration SQL when possible. PostgreSQL supports transactional DDL, so failed migrations will be fully rolled back.

## Notes

- Must be run from inside the `jetbase/` directory
- Cannot use both `--count` and `--to-version` together
- The lock prevents concurrent migrations from causing conflicts

## See Also

- [`rollback`](rollback.md) — Undo migrations
- [`status`](status.md) — Check pending migrations
- [`history`](history.md) — View applied migrations
- [Writing Migrations](../migrations/writing-migrations.md) — Learn migration syntax
