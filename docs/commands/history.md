# jetbase history

Shows you which migrations have been applied to your database, and the exact time each one was applied.

## Usage

```bash
jetbase history
```

## Description

The `history` command displays a detailed table of all migrations that have been applied to the database, including when they were applied and in what order. This is useful for auditing and understanding the evolution of your database schema.

## Output

The command displays a formatted table with:

- **Version** — The migration version number
- **Order Executed** — The sequence in which the migration was applied
- **Description** — The migration description (from the filename)
- **Applied At** — The timestamp when the migration was applied

## Examples

### Basic Usage

```bash
jetbase history
```

### Typical Output

```
                              Migration History
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Order Executed ┃ Description            ┃ Applied At             ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1                 │ 1              │ create_users_table     │ 2025-12-20 10:15:32.12 │
│ 2                 │ 2              │ add_email_to_users     │ 2025-12-21 09:45:18.54 │
│ 3                 │ 3              │ create_orders_table    │ 2025-12-22 14:22:07.89 │
└───────────────────┴────────────────┴────────────────────────┴────────────────────────┘
```

### When No Migrations Have Been Applied

```bash
jetbase history
```

Output:

```
No migrations have been applied yet.
```

## Understanding the Output

### Version Column

- **Versioned migrations** show the version (e.g., `20251220.100000`, `2.4`)
- **Repeatable migrations** show their type (see [Migration Types](../advanced/migration-types.md)):
  - `RUNS_ALWAYS`
  - `RUNS_ON_CHANGE`


### Order Executed

The sequential order in which migrations were applied to the database. This is useful for:

- Understanding the timeline of changes
- Debugging issues that appeared after a specific migration
- Auditing purposes
- For repeatable migrations, the order executed that is displayed will show the order during first time it was run (the applied at section will show the most recent timestamp of when it was run)

### Applied At

The exact timestamp when the migration was applied. The format is:

```
YYYY-MM-DD HH:MM:SS.microseconds
```

## Notes

- Must be run from inside the `jetbase/` directory

