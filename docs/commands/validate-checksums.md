# jetbase validate-checksums

Verify that migration files haven't been modified since they were applied.

## What Is a Checksum?

A checksum is a unique "fingerprint" calculated from the contents of your migration file. When you apply a migration, Jetbase stores this fingerprint. Later, it can verify the file hasn't changed by recalculating the fingerprint and comparing.


## Usage

```bash
jetbase validate-checksums
```

```

## Options

| Option  | Short | Description                                    |
| ------- | ----- | ---------------------------------------------- |
| `--fix` | `-f`  | Update stored checksums to match current files |
```

> **Tip:**  
> You can use either  
> 
> ```
> jetbase validate-checksums --fix
> ```
> or the shortcut:
> ```
> jetbase fix-checksums
> ```
> 
> Both commands are **identical** 

## Description

The `validate-checksums` command compares the checksums of your migration files against the checksums stored in the database. This helps detect if someone has modified a migration file after it was applied, which could indicate:

- Accidental edits to applied migrations
- Intentional changes that need to be handled
- File corruption

When working with AI agents to generate or manage code, it's easy for files to be changed in ways you might not expect. For example, an agent could accidentally revise an old migration file instead of creating a new one when implementing a new feature.

This kind of modification can be risky: without proper checksum validation, the altered migration might not run, leading to differences ("drift") between environments such as local, development, staging, and production.

In these situations, some environments may end up applying the old version of a migration file, while others run the new one—resulting in inconsistent database schemas across your projects. Regular checksum validation helps catch these issues early and is especially important when collaborating with both developers and AI agents.


## Examples

### Audit Mode (Default)

Check for checksum mismatches without making changes:

```bash
jetbase validate-checksums
```

**If all checksums match:**

```
All migration checksums are valid - no altered upgrade statments detected.
```

**If mismatches are found:**

```
JETBASE - Checksum Audit Report
----------------------------------------
Changes detected in the following files:
 → 3
 → 7
```

### Fix Mode

Update stored checksums to match the current file contents:

```bash
jetbase validate-checksums --fix
```

Output:

```
Fixed checksum for version: 3
Fixed checksum for version: 7
```



```
Original file → Checksum: abc123
Modified file → Checksum: xyz789  ← Different! File was changed
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


## Notes

- Must be run from inside the `jetbase/` directory
- Only validates migrations that have been applied
- Only uses upgrade SQL statements in the migration file to calculate checksums

