# jetbase fix

Repair migration files and checksums in one command.

## Usage

```bash
jetbase fix
```

## Description

The `fix` command is a convenience command that repairs both file issues and checksum issues. It's equivalent to running:

```bash
jetbase validate-files --fix
jetbase validate-checksums --fix
```

Use this when you want to quickly resolve migration drift without running multiple commands.

## What It Fixes

### 1. Missing Files

Removes database records for migrations whose files no longer exist.

Example:

```
Stopped tracking the following missing versions:
→ 20251225.143022
```

### 2. Checksum Mismatches

Updates stored checksums to match the current content of migration files.

Example:

```
Fixed checksum for version: 20251225.150000
```

## Examples

### Basic Usage

```bash
jetbase fix
```

Typical output:

```
Stopped tracking the following missing versions:
→ 20251225.143022
Fixed checksum for version: 20251225.150000
```

### When Nothing Needs Fixing

```bash
jetbase fix
```

Output:

```
No missing migration files.
All migration checksums are already valid - no drift detected.
```

## When to Use

### Quick Cleanup

When you know there are issues and want to fix them all at once:

```bash
# Don't know exactly what's wrong, just fix it
jetbase fix
```

### After Major Changes

After reorganizing migrations or resolving merge conflicts:

```bash
# After a complicated merge
jetbase fix

# Then verify everything is good
jetbase status
```

### Development Reset

When cleaning up after experiments:

```bash
# Clear out development mess
jetbase fix
jetbase upgrade
```

## Comparison with Individual Commands

| Command                    | Use Case                   |
| -------------------------- | -------------------------- |
| `validate-files`           | Audit missing files only   |
| `validate-files --fix`     | Fix missing files only     |
| `validate-checksums`       | Audit checksum issues only |
| `validate-checksums --fix` | Fix checksum issues only   |
| `fix`                      | Fix both at once           |

### When to Use `fix` vs Individual Commands

**Use `fix` when:**

- You want to fix everything quickly
- You're in development and don't need detailed auditing
- You've already audited and know what needs fixing

**Use individual commands when:**

- You want to audit before fixing
- You only want to fix one type of issue
- You want more control over what changes

## Safety Considerations

!!! warning "Understand Before Fixing"
The `fix` command makes changes to your database records. Before running it:

    1. Run `jetbase validate-files` to see missing files
    2. Run `jetbase validate-checksums` to see checksum mismatches
    3. Make sure you understand why the issues exist
    4. Then run `jetbase fix` if appropriate

### When NOT to Use `fix`

- **In production** without understanding the issues first
- **Before rollback** (you might need those files)
- **When files might exist elsewhere** (other branches, team members)

## Notes

- Must be run from inside the `jetbase/` directory
- Runs both fixes sequentially (files first, then checksums)
- Cannot be undone without database backups

## See Also

- [`validate-files`](validate-files.md) — Audit or fix missing files
- [`validate-checksums`](validate-checksums.md) — Audit or fix checksum issues
- [Troubleshooting](../troubleshooting.md) — Common issues and solutions
