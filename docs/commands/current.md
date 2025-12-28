# jetbase current

Show the latest applied migration version.

## Usage

```bash
jetbase current
```

## Description

The `current` command displays the version number of the most recently applied migration. It's a quick way to check where your database schema currently stands.

## Output

### When Migrations Have Been Applied

```bash
jetbase current
```

Output:

```
Latest migration version: 20251225.143022
```

### When No Migrations Have Been Applied

```bash
jetbase current
```

Output:

```
No migrations have been applied yet.
```

## Examples

### Quick Version Check

```bash
jetbase current
```

### Use in Scripts

You can use `current` in deployment scripts to verify the database state:

```bash
#!/bin/bash

# Get current version before deploying
echo "Current database version:"
jetbase current

# Deploy new code
# ...

# Apply new migrations
jetbase upgrade

# Verify new version
echo "New database version:"
jetbase current
```

## Common Use Cases

### Before Deployment

```bash
# Quick check of current state
jetbase current

# Then check what's pending
jetbase status
```

### After Deployment

```bash
# Verify migrations were applied
jetbase current
```

### Debugging

```bash
# Quick check during troubleshooting
jetbase current

# For more details, use history
jetbase history
```

## Comparison with Other Status Commands

| Command   | Use Case                           |
| --------- | ---------------------------------- |
| `current` | Quick version number check         |
| `status`  | See applied and pending migrations |
| `history` | Full audit trail with timestamps   |

## Notes

- Must be run from inside the `jetbase/` directory
- Shows only the version of the latest **versioned** migration
- Does not show repeatable migrations

## See Also

- [`status`](status.md) — View complete migration status
- [`history`](history.md) — View detailed migration history
- [`upgrade`](upgrade.md) — Apply pending migrations
