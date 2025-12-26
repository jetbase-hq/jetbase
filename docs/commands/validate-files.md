# jetbase validate-files

Check for missing migration files.

## Usage

```bash
jetbase validate-files [OPTIONS]
```

## Description

The `validate-files` command checks if all migrations recorded in the database still have their corresponding SQL files. This helps detect when migration files have been accidentally deleted or moved.

## Options

| Option  | Short | Description                               |
| ------- | ----- | ----------------------------------------- |
| `--fix` | `-f`  | Remove database records for missing files |

## Examples

### Audit Mode (Default)

Check for missing files without making changes:

```bash
jetbase validate-files
```

**If all files exist:**

```
All migrations have corresponding files.
```

**If files are missing:**

```
The following migrations are missing their corresponding files:
→ 20251225.143022
→ 20251225.150000
→ ROC__stored_procedures.sql
```

### Fix Mode

Remove records of migrations whose files no longer exist:

```bash
jetbase validate-files --fix
jetbase validate-files -f
```

Output:

```
Stopped tracking the following missing versions:
→ 20251225.143022
→ 20251225.150000
Removed the following missing repeatable migrations from the database:
→ ROC__stored_procedures.sql
```

## When to Use

### After Accidental Deletion

If you accidentally deleted a migration file:

```bash
# Check what's missing
jetbase validate-files

# Option 1: Restore from git
git checkout -- migrations/V20251225.143022__create_users.sql

# Option 2: Remove the database record
jetbase validate-files --fix
```

### Before Rollback

Rollback requires the migration files to exist. Check first:

```bash
jetbase validate-files

# If files are missing, restore them or fix records
```

### After Branch Switching

When switching git branches, some migration files might not exist:

```bash
# Check if current branch has all files
jetbase validate-files
```

## Why This Matters

### Rollback Safety

You can't roll back a migration if the file doesn't exist:

```bash
jetbase rollback
# Error: Migration file for version '20251225.143022' not found
```

### Database Integrity

Missing files can indicate:

- Accidental deletions
- Incomplete git operations
- Merge conflicts that removed files

### Team Coordination

Helps identify when:

- Someone forgot to commit new migrations
- Files were removed in a PR that shouldn't have been

## What `--fix` Does

When you run `validate-files --fix`:

1. **Identifies** migrations without corresponding files
2. **Removes** those records from the database
3. **Reports** what was removed

!!! warning
Using `--fix` means Jetbase will forget those migrations ever happened. The database changes from those migrations remain, but Jetbase won't track them anymore.

### When to Use `--fix`

✅ **Safe to fix when:**

- The migration was applied but never committed (development only)
- The file was intentionally removed and won't be needed
- You're cleaning up after a failed experiment

❌ **Don't fix when:**

- You need to roll back those migrations later
- Other team members might have the files
- You're not sure why the files are missing

## Common Scenarios

### Development Cleanup

```bash
# After experimenting with migrations
jetbase validate-files
# Shows missing files from deleted experiments

jetbase validate-files --fix
# Clean up the records
```

### Production Issue

```bash
# Check for missing files before deployment
jetbase validate-files

# If files are missing, DON'T use --fix
# Instead, restore the files from your repository
```

### Git Branch Issues

```bash
# Switched branches, migrations might be different
jetbase validate-files

# If files are missing, switch back or restore them
```

## Notes

- Must be run from inside the `jetbase/` directory
- Checks both versioned and repeatable migrations
- Using `--fix` is irreversible (without database backup)

## See Also

- [`validate-checksums`](validate-checksums.md) — Check for modified migration files
- [`fix`](fix.md) — Fix both file and checksum issues
- [`rollback`](rollback.md) — Understand why files are needed
