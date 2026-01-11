# jetbase upgrade

Apply pending migrations to your database.

## Usage

```bash
jetbase upgrade
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
```

### Apply Up to a Specific Version

```bash
# Apply all migrations up to and including version 5
jetbase upgrade --to-version 5
```


### Preview Changes (Dry Run)

```bash
jetbase upgrade --dry-run
```

This shows you what migrations would be applied without actually running them. Great for verifying before deployment!

Output example:

```
=== DRY RUN MODE ===
The following migrations would be applied:

--- V1__create_users_table.sql ---
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL
);

--- V2__add_email_to_users.sql ---
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
    To learn more, see [Validations](../validations/index.md).


## Migration Types

During upgrade, Jetbase processes three types of migrations. Most developers will only ever need to worry about the standard Versioned Migrations. 

### Versioned Migrations (`V*`)

Standard migrations that run once, in version order.

```
V20251225.143022__create_users_table.sql
```

### Runs Always (`RA__*`)

Migrations that run on every upgrade.

```
RA__refresh_views.sql
```

### Runs On Change (`ROC__*`)

Migrations that run only when the file content changes.

```
ROC__update_view.sql
```

Learn more in [Migration Types](../advanced/migration-types.md).



## Error Handling

Jetbase is designed to keep your database safe even when something goes wrong. If a migration fails during an upgrade:

1. **No Partial Changes:** The failed migration file will *not* be applied at all. Any statements within that file are rolled back, so your database remains unchanged by that migration.
2. **Orderly Progress:** All prior migration files that completed successfully in during that same upgrade command remain applied. Any migration files scheduled to run *after* the failed one are skipped.
3. **Clear Feedback:** You’ll see a descriptive error message explaining what went wrong, so you can fix the issue and try again.

Jetbase stops safely at the first sign of trouble, preventing partial or out-of-order migrations.


## Notes

- Must be run from inside the `jetbase/` directory
- Cannot use both `--count` and `--to-version` together
- The automatic lock prevents concurrent migrations from causing conflicts

