# jetbase validate-checksums

Verify that migration files haven't been modified since they were applied.

## Usage

```bash
jetbase validate-checksums [OPTIONS]
```

## Description

The `validate-checksums` command compares the checksums of your migration files against the checksums stored in the database. This helps detect if someone has modified a migration file after it was applied, which could indicate:

- Accidental edits to applied migrations
- Intentional changes that need to be handled
- File corruption

## Options

| Option  | Short | Description                                    |
| ------- | ----- | ---------------------------------------------- |
| `--fix` | `-f`  | Update stored checksums to match current files |

## Examples

### Audit Mode (Default)

Check for checksum mismatches without making changes:

```bash
jetbase validate-checksums
```

**If all checksums match:**

```
All migration checksums are already valid - no drift detected.
```

**If mismatches are found:**

```
JETBASE - Checksum Audit Report
----------------------------------------
Changes detected in the following files:
 → 20251225.143022
 → 20251225.150000
```

### Fix Mode

Update stored checksums to match the current file contents:

```bash
jetbase validate-checksums --fix
jetbase validate-checksums -f
```

Output:

```
Fixed checksum for version: 20251225.143022
Fixed checksum for version: 20251225.150000
```

## What Is a Checksum?

A checksum is a unique "fingerprint" calculated from the contents of your migration file. When you apply a migration, Jetbase stores this fingerprint. Later, it can verify the file hasn't changed by recalculating the fingerprint and comparing.

```
Original file → Checksum: abc123
Modified file → Checksum: xyz789  ← Different! File was changed
```

## When to Use

### Regular Audits

Run periodically to catch accidental changes:

```bash
# In CI/CD or as a pre-deployment check
jetbase validate-checksums
```

### After Intentional Changes

If you intentionally modified an applied migration:

```bash
# Verify what changed
jetbase validate-checksums

# If the changes are intentional, update the checksums
jetbase validate-checksums --fix
```

### Debugging Migration Issues

```bash
# Check if files have drifted
jetbase validate-checksums
```

## Why Do Checksums Matter?

### Preventing Confusion

If a migration file is modified after being applied:

- **The database** has the original changes
- **The file** has different content
- **Future deployments** might be confusing

### Team Coordination

Checksums help catch when:

- Someone edits an already-applied migration instead of creating a new one
- Merge conflicts corrupt a migration file
- Local changes weren't properly committed

### Best Practices

1. **Never modify applied migrations** — Always create new migrations for changes
2. **Run checksum validation in CI/CD** — Catch issues before deployment
3. **Use `--fix` sparingly** — Only when you understand why the mismatch exists

## Common Scenarios

### Accidental Edit

```bash
# Someone accidentally edited an applied migration
jetbase validate-checksums
# Shows: Changes detected in 20251225.143022

# Option 1: Restore the original file from git
git checkout -- migrations/V20251225.143022__create_users.sql

# Option 2: If the change was intentional
jetbase validate-checksums --fix
```

### After Git Merge

```bash
# After a merge, verify nothing was corrupted
jetbase validate-checksums
```

### CI/CD Check

```yaml
# In your CI pipeline
- name: Validate migrations
  run: |
    cd jetbase
    jetbase validate-checksums
```

## Notes

- Must be run from inside the `jetbase/` directory
- Only validates migrations that have been applied
- Uses the `-- upgrade` section of files to calculate checksums

## See Also

- [`validate-files`](validate-files.md) — Check for missing migration files
- [`fix`](fix.md) — Fix both checksum and file issues
- [Writing Migrations](../migrations/writing-migrations.md) — Best practices for migrations
