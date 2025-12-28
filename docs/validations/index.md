# Validations

Jetbase performs several validations before applying migrations to ensure database integrity and prevent common mistakes. These checks run automatically during `jetbase upgrade` and help catch issues before they cause problems in your database.

Jetbase's validations act as guardrails to:

- **Prevent accidental changes** to already-applied migrations
- **Ensure migration order** is consistent across environments
- **Catch missing files** before they cause failures / drift across environments (dev, staging, production)
- **Detect conflicts** when multiple AI agents / developers add migrations

## Validation Types

Jetbase performs two categories of validations:

| Category | Config to Skip | What It Checks |
|----------|----------------|----------------|
| **File Validation** | `skip_file_validation` | Migration file presence and ordering |
| **Checksum Validation** | `skip_checksum_validation` | File content integrity |

You can also use `skip_validation` to skip **all** validations at once.

---

## File Validations

These validations ensure your migration files are properly organized and haven't been removed.

### 1. Out-of-Order Migration Check

**What it checks:** New migration files must have a version higher than the last applied migration.

**Why it matters:** Migrations are applied in version order. If you add a migration with a lower version than one already applied, it would never run. Jetbase can automatically catch this issue before it causes problems.

**Example error:**
```
V2.4__add_users.sql has version 20240103 which is lower than the 
latest migrated version 3.1.
New migration files cannot have versions lower than the latest migrated version.
Please rename the file to have a version higher than 3.1.
```

**How to fix:** Rename your migration file to have a version higher than the latest applied migration.

---

### 2. Missing Migration Files Check

**What it checks:** Every previously applied migration must still have its corresponding file in the migrations directory.

**Why it matters:** If a migration file is deleted, Jetbase can't verify what was applied or perform rollbacks. This also indicates potential sync issues between environments.

**Example error:**
```
Version 2.4 has been migrated but is missing from the current migration files.
```

**How to fix:** Restore the missing migration file, or if intentionally removed, use `jetbase fix-files` to update the migration history.

---


### 3. Duplicate Version Check

**What it checks:** No two migration files can have the same version number.

**Why it matters:** Duplicate versions create ambiguity—Jetbase wouldn't know which migration to apply first, and different environments could end up with different schemas.

**Example error:**
```
Duplicate migration version detected: 2.4.
Each file must have a unique version.
Please rename the file to have a unique version.
```

**How to fix:** Rename one of the duplicate files to have a unique version.

!!! note
    This validation **always runs** and cannot be skipped.

---

## Checksum Validation

### File Content Integrity Check

**What it checks:** Applied migration files haven't been modified since they were run.

**Why it matters:** Changing an already-applied migration is dangerous because:

- The database already has the **old** version applied
- Other environments will apply the **new** version
- You end up with inconsistent schemas across environments

Jetbase calculates a SHA-256 checksum of each migration's SQL statements and stores it when the migration is applied. On subsequent upgrades, it recalculates and compares to make sure the sql statements in the have not changeds.

#### AI and Migration File Modifications

When working with AI agents to generate or manage code, it's easy for files to be changed in ways you might not expect. For example, an agent could accidentally revise an old migration file instead of creating a new one when implementing a new feature.

This kind of modification can be risky: without proper checksum validation, the altered migration might not run, leading to differences ("drift") between environments such as local, development, staging, and production.

In these situations, some environments may end up applying the old version of a migration file, while others run the new one—resulting in inconsistent database schemas across your projects. Regular checksum validation helps catch these issues early and is especially important when collaborating with both humans and AI.

**Example error:**
```
Checksum mismatch for versions: 2.4, 3.1. 
Files have been changed since migration.
```

**How to fix:**

1. **Revert your changes** if they were accidental
2. **if you need to make schema changes** revert your changes in those files and instead make the changes in a new migration file
3. **Use `jetbase fix-checksums`** if you intentionally modified the files and understand the risks

---

## Skipping Validations

!!! warning "Use with caution"
    Skipping validations can lead to inconsistent database states. Only skip if you fully understand the implications.

### Via Command Line

```bash
# Skip all validations
jetbase upgrade --skip-validation

# Skip only file validation
jetbase upgrade --skip-file-validation

# Skip only checksum validation
jetbase upgrade --skip-checksum-validation
```

### Via Configuration

```python
# jetbase/env.py
skip_validation = True           # Skip all
skip_file_validation = True      # Skip file checks only
skip_checksum_validation = True  # Skip checksum checks only
```

---

## Validation Commands

Jetbase provides commands to check validations without running migrations:

| Command | Description |
|---------|-------------|
| `jetbase validate-checksums` | Check for checksum mismatches |
| `jetbase validate-checksums --fix` | Fix checksum mismatches by updating stored checksums |
| `jetbase validate-files` | Check for missing or out-of-order files |
| `jetbase fix-checksums` | Alias for `validate-checksums --fix` |

---

## Best Practices

1. **Never modify applied migration files** — Create new migrations instead
2. **Don't delete migration files** — Keep your full migration history
3. **Address validation errors immediately** — Don't skip validations as a workaround

