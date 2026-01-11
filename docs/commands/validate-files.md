# jetbase validate-files

Check for missing migration files, out of order migrations, and if files have 

## Usage

```bash
jetbase validate-files
```

## Description

The `validate-files` command performs the following checks:

- Ensures every migration recorded in the database still has its corresponding SQL file (detects missing, deleted, or moved files)
- Warns if any new migration file has a lower version than those already migrated (out-of-order migrations)
- Verifies that all migration versions are unique (prevents duplicates)

For detailed explanations of these checks, see [Validations](../validations/index.md).

## Options

| Option  | Short | Description                               |
| ------- | ----- | ----------------------------------------- |
| `--fix` | `-f`  | Remove database records for missing files |

> **Tip:**  
> You can use either  
> 
> ```
> jetbase validate-files --fix
> ```
> or the shortcut:
> ```
> jetbase fix-files
> ```
> 
> Both commands are **identical** 

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
→ 4
→ 9
```

### Fix Mode

Remove records of migrations whose files no longer exist:

```bash
jetbase validate-files --fix
```

Output:

```
Stopped tracking the following missing versions:
→ 4
→ 9
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

- The file was intentionally removed and won't be needed
- You're cleaning up after a failed experiment

❌ **Don't fix when:**

- You need to roll back those migrations later
- Other team members might have the files
- You're not sure why the files are missing

