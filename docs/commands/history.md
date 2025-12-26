# jetbase history

Show the complete migration history.

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
│ 20251220.100000   │ 1              │ create_users_table     │ 2025-12-20 10:15:32.12 │
│ 20251221.093000   │ 2              │ add_email_to_users     │ 2025-12-21 09:45:18.54 │
│ 20251222.140000   │ 3              │ create_orders_table    │ 2025-12-22 14:22:07.89 │
│ [ROC]             │ 4              │ stored_procedures      │ 2025-12-23 08:30:45.23 │
│ [RA]              │ 5              │ refresh_views          │ 2025-12-24 16:12:33.67 │
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

- **Versioned migrations** show the timestamp version (e.g., `20251220.100000`)
- **Repeatable migrations** show their type prefix:
  - `[ROC]` — Repeatable On Change
  - `[RA]` — Repeatable Always

### Order Executed

The sequential order in which migrations were applied to the database. This is useful for:

- Understanding the timeline of changes
- Debugging issues that appeared after a specific migration
- Auditing purposes

### Applied At

The exact timestamp when the migration was applied. The format is:

```
YYYY-MM-DD HH:MM:SS.microseconds
```

## Common Use Cases

### Audit Trail

```bash
# View complete history for compliance/auditing
jetbase history
```

### Debugging

```bash
# Find when a specific change was made
jetbase history
# Look for the migration that might have caused an issue
```

### Team Coordination

```bash
# Check what migrations teammates have applied
jetbase history
```

### Deployment Verification

```bash
# Verify migrations were applied after deployment
jetbase history
```

## Difference from `status`

| Command   | Shows                                                |
| --------- | ---------------------------------------------------- |
| `status`  | Applied and **pending** migrations                   |
| `history` | Only applied migrations with **detailed timestamps** |

Use `status` to see what needs to be done. Use `history` for a detailed audit trail.

## Notes

- Must be run from inside the `jetbase/` directory
- Shows migrations from the `jetbase_migrations` database table
- Results are ordered by execution order (ascending)

## See Also

- [`status`](status.md) — View applied and pending migrations
- [`current`](current.md) — Quick check of the latest version
- [`upgrade`](upgrade.md) — Apply new migrations
