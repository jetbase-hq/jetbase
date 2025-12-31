# Commands Reference 🛠️

Jetbase provides a set of intuitive commands to manage your database migrations. This section covers all available commands and their options.

## Quick Reference

| Command                                       | Description                                                        |
| --------------------------------------------- | ------------------------------------------------------------------ |
| [`init`](init.md)                             | Initialize Jetbase in current directory                            |
| [`new`](new.md)                               | Create a new migration file                                        |
| [`upgrade`](upgrade.md)                       | Apply pending migrations                                           |
| [`rollback`](rollback.md)                     | Undo migrations                                                    |
| [`status`](status.md)                         | Show migration status of all migration files (applied vs. pending) |
| [`history`](history.md)                       | Show migration history                                             |
| [`current`](current.md)                       | Show latest version migrated                                       |
| [`lock-status`](lock-status.md)               | Check if migrations are locked                                     |
| [`unlock`](unlock.md)                         | Remove migration lock                                              |
| [`validate-checksums`](validate-checksums.md) | Verify migration file integrity                                    |
| [`validate-files`](validate-files.md)         | Check for missing migration files                                  |
| [`fix`](fix.md)                               | Fix migration issues                                               |
| [`fix-files`](validate-files.md)              | Fix missing migration files (same as `validate-files --fix`)       |
| [`fix-checksums`](validate-checksums.md)      | Fix migration file checksums (same as `validate-checksums --fix`)  |

## Command Categories

### 🚀 Setup Commands

Commands to initialize and set up your migration environment:

- **[`init`](init.md)** — Create the Jetbase directory structure

### 📝 Migration Commands

Commands to create and run migrations:

- **[`new`](new.md)** — Generate a new migration file
- **[`upgrade`](upgrade.md)** — Apply pending migrations to the database
- **[`rollback`](rollback.md)** — Undo one or more migrations

### 📊 Status Commands

Commands to check the state of your migrations:

- **[`status`](status.md)** — See applied and pending migrations
- **[`history`](history.md)** — View complete migration history
- **[`current`](current.md)** — Show the latest applied version

### 🔒 Lock Commands

Commands to manage migration locking:

- **[`lock-status`](lock-status.md)** — Check if the database is locked
- **[`unlock`](unlock.md)** — Manually release the migration lock

### 🔧 Maintenance Commands

Commands to validate and fix migration issues:

- **[`validate-checksums`](validate-checksums.md)** — Check for modified migration files
- **[`validate-files`](validate-files.md)** — Check for missing files
- **[`fix`](fix.md)** — Automatically repair common issues

## Getting Help

Every command has a `--help` option:

```bash
jetbase --help           # General help
jetbase upgrade --help   # Help for upgrade command
jetbase rollback --help  # Help for rollback command
```
