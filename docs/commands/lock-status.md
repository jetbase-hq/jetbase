# jetbase lock-status

Check if the database migration lock is active.

## Usage

```bash
jetbase lock-status
```

## Description

The `lock-status` command shows whether the database is currently locked for migrations. Jetbase uses a locking mechanism to prevent multiple migration processes from running simultaneously, which could cause database corruption.

## Output

### When Unlocked (Normal State)

```bash
jetbase lock-status
```

Output:

```
Status: UNLOCKED
```

This is the normal state. You can safely run migrations.

### When Locked

```bash
jetbase lock-status
```

Output:

```
Status: LOCKED
Locked At: 2025-12-25 14:30:22.123456
```

This means a migration process is (or was) running. Wait for it to complete or investigate if you suspect the lock is stale.

## How Locking Works

1. **Before migrations run**, Jetbase acquires a lock in the `jetbase_lock` table
2. **During migrations**, the lock prevents other processes from starting migrations
3. **After migrations complete**, the lock is automatically released

```
Process A: acquire lock → run migrations → release lock
Process B:              wait...           → acquire lock → run...
```

## Common Scenarios

### Normal Operation

```bash
# Check before running migrations
jetbase lock-status
# Status: UNLOCKED

# Run migrations
jetbase upgrade
# Migrations complete successfully

# Lock is automatically released
jetbase lock-status
# Status: UNLOCKED
```

### Concurrent Processes

If two processes try to run migrations simultaneously:

```bash
# Terminal 1
jetbase upgrade
# Acquires lock and starts running...

# Terminal 2
jetbase upgrade
# Waits for lock or fails
```

### Stale Lock (After Crash)

If a migration process crashes without releasing the lock:

```bash
jetbase lock-status
# Status: LOCKED
# Locked At: 2025-12-25 14:30:22.123456

# After confirming no migration is running:
jetbase unlock
# Unlock successful.
```

## When to Check Lock Status

- **Before investigating issues** — Check if a migration is in progress
- **After a crash** — See if a lock was left behind
- **In CI/CD pipelines** — Verify state before deploying
- **When migrations hang** — Determine if another process has the lock

## Troubleshooting

### Lock Is Stuck

If the lock shows as `LOCKED` but you're sure no migration is running:

1. **Check for running processes**:

   ```bash
   ps aux | grep jetbase
   ```

2. **Check database connections**:

   ```sql
   -- PostgreSQL
   SELECT * FROM pg_stat_activity WHERE query LIKE '%jetbase%';
   ```

3. **If safe, unlock manually**:
   ```bash
   jetbase unlock
   ```

!!! warning
Only use `jetbase unlock` if you're **certain** no migration is currently running. Unlocking during an active migration can cause database corruption.

## Notes

- Must be run from inside the `jetbase/` directory
- The lock is stored in the `jetbase_lock` database table
- Locks are automatically released on successful migration completion

## See Also

- [`unlock`](unlock.md) — Manually release a stuck lock
- [`upgrade`](upgrade.md) — Run migrations
- [Troubleshooting](../troubleshooting.md) — Common issues and solutions
