# jetbase unlock

Manually release the migration lock.

## Usage

```bash
jetbase unlock
```

## Description

The `unlock` command forcefully releases the migration lock, allowing migrations to run again. This should only be used when you're certain that no migration is currently in progress.

!!! danger "Use With Caution"
Running `unlock` while a migration is actually in progress can lead to **database corruption**. Only use this command when you're absolutely certain no migration process is running.

## Output

```bash
jetbase unlock
```

Output:

```
Unlock successful.
```

## When to Use

### ✅ Safe to Unlock

- The lock is stale from a crashed process
- You've verified no migration is running (checked processes, database connections)
- You're in a development environment and want to reset state

### ❌ Do NOT Unlock If

- A migration might still be running
- You're unsure what's happening
- Other team members might be running migrations

## Before Unlocking

Always verify the situation before unlocking:

### 1. Check Lock Status

```bash
jetbase lock-status
```

### 2. Look for Running Processes

```bash
# Check for jetbase processes
ps aux | grep jetbase

# Check for database connections (PostgreSQL)
psql -c "SELECT * FROM pg_stat_activity WHERE application_name LIKE '%jetbase%';"
```

### 3. Check with Team Members

If working in a team, make sure no one else is running migrations.

## Examples

### Recovery After Crash

```bash
# Process crashed during migration
jetbase lock-status
# Status: LOCKED
# Locked At: 2025-12-25 14:30:22

# Verify no migration is running
ps aux | grep jetbase
# (no results)

# Safe to unlock
jetbase unlock
# Unlock successful.

# Retry the migration
jetbase upgrade
```

### Development Reset

```bash
# In development, reset everything
jetbase unlock
jetbase upgrade
```

## What Happens Internally

The `unlock` command:

1. Connects to the database
2. Updates the `jetbase_lock` table to release the lock
3. Confirms the unlock was successful

The lock table looks like:

```sql
-- When locked
| is_locked | locked_at                  |
|-----------|----------------------------|
| true      | 2025-12-25 14:30:22.123456 |

-- After unlock
| is_locked | locked_at |
|-----------|-----------|
| false     | null      |
```

## Alternative Solutions

Before using `unlock`, consider these alternatives:

### Wait for the Lock to Release

If a migration is running, it will release the lock when complete. Be patient.

### Restart the Database Connection

Sometimes reconnecting helps if there's a stale connection.

### Check for Long-Running Queries

```sql
-- PostgreSQL: Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
```

## Notes

- Must be run from inside the `jetbase/` directory
- Always verify no migration is running before unlocking
- In CI/CD, consider adding a timeout or retry logic instead of immediate unlock

## See Also

- [`lock-status`](lock-status.md) — Check if the database is locked
- [`upgrade`](upgrade.md) — Run migrations
- [Troubleshooting](../troubleshooting.md) — Common issues and solutions
