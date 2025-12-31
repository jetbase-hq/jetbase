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

This indicates that a migration process is currently in progress. Please wait for it to finish before attempting any further actions. 

If you are absolutely certain that no migration or fix command is active, you may use `jetbase unlock` to safely release the lock (see [`unlock`](unlock.md) for details).

## How Locking Works

1. **Before migrations run**, Jetbase locks other migrations from running
2. **During migrations**, the lock prevents other processes from starting migrations
3. **After migrations complete**, the lock is automatically released

For a detailed explanation of how migration locking works, see [Migration Locking](../advanced/migration-locking.md).


- Must be run from inside the `jetbase/` directory
- The lock is stored in the `jetbase_lock` database table
- Locks are automatically released whether the migration was successful or an error occurred.

