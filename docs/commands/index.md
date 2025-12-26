# Commands Reference 🛠️

Jetbase provides a set of intuitive commands to manage your database migrations. This section covers all available commands and their options.

## Quick Reference

| Command                                       | Description                             |
| --------------------------------------------- | --------------------------------------- |
| [`init`](init.md)                             | Initialize Jetbase in current directory |
| [`new`](new.md)                               | Create a new migration file             |
| [`upgrade`](upgrade.md)                       | Apply pending migrations                |
| [`rollback`](rollback.md)                     | Undo migrations                         |
| [`status`](status.md)                         | Show migration status                   |
| [`history`](history.md)                       | Show migration history                  |
| [`current`](current.md)                       | Show current migration version          |
| [`lock-status`](lock-status.md)               | Check if migrations are locked          |
| [`unlock`](unlock.md)                         | Remove migration lock                   |
| [`validate-checksums`](validate-checksums.md) | Verify migration file integrity         |
| [`validate-files`](validate-files.md)         | Check for missing migration files       |
| [`fix`](fix.md)                               | Repair migration issues                 |

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

## Common Patterns

### First-Time Setup

```bash
# Initialize Jetbase
jetbase init

# Navigate to jetbase directory
cd jetbase

# Edit env.py with your database connection
# Then create your first migration
jetbase new "initial schema"

# Apply migrations
jetbase upgrade
```

### Daily Workflow

```bash
# Check what needs to be done
jetbase status

# Create a new migration
jetbase new "add email to users"

# Apply it
jetbase upgrade
```

### Fixing Issues

```bash
# Made a mistake? Roll back
jetbase rollback

# Modified a migration file? Fix checksums
jetbase fix-checksums

# Deleted a migration file? Fix files
jetbase fix-files

# Or fix everything at once
jetbase fix
```

### Checking Status

```bash
# Quick current version
jetbase current

# Full status
jetbase status

# Complete history
jetbase history
```

## Getting Help

Every command has a `--help` option:

```bash
jetbase --help           # General help
jetbase upgrade --help   # Help for upgrade command
jetbase rollback --help  # Help for rollback command
```
