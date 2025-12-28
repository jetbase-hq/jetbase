# Migration Locking

Suppose two developers or AI agents both run `jetbase upgrade` at the same time.

Without any locking, both processes could try to change the database together. This might cause errors, data corruption, or broken migrations.

Jetbase solves this with **automatic migration locking**. Only one process can run migrations at a time. 

## What Is Migration Locking?

When you run `jetbase upgrade`, Jetbase grabs a lock before touching your database. Think of it like putting a "Do Not Disturb" sign on your migrations. No other process can run migrations until the first one finishes.

Jetbase automatically acquires a lock whenever you run any command that might modify the `jetbase_migrations` table. This includes commands like `jetbase upgrade`, `jetbase rollback`, and all `fix` operations. By doing this, Jetbase ensures that your migrations always run safely without any risk of collision.

You shouldn't need to think about locking at all! With Jetbase, it just works out of the box!


```
┌──────────────┐                     ┌──────────────┐
│  Process A   │                     │  Process B   │
└──────┬───────┘                     └──────┬───────┘
       │                                    │
       ▼                                    │
   🔒 Acquire lock                          │
       │                                    │
       ▼                                    ▼
   Run migrations               🚫 "Lock is held, please try again later"
       │                                    │
       ▼                                    │
   🔓 Release lock ─────────────────────────┤
       │                                    │
       ▼                                    ▼
     Done!                            🔄 Retry
                                            │
                                            ▼
                                      🔒 Acquire lock
                                            │
                                            ▼
                                       Run migrations
                                            │
                                            ▼
                                      🔓 Release lock
                                            │
                                            ▼
                                          Done!
```

## Why Does This Matter?

Without locking, bad things can happen:

| Scenario | What Goes Wrong |
|----------|-----------------|
| Two AI agents or developers attempt to run migrations simultaneously | Each agent might attempt conflicting schema changes or partial upgrades, risking schema drift or inconsistent data |
| Multiple app instances start simultaneously |  Migration history gets corrupted |
| Two CI/CD pipelines deploy at once | Both try to create the same table → one fails |

Locking ensures **exactly one** migration process runs at a time. Simple as that.

## How It Works

Jetbase stores lock state in a `jetbase_lock` table in your database:

| Column | Description |
|--------|-------------|
| `is_locked` | `true` when migrations are running |
| `locked_at` | Timestamp when the lock was acquired |
| `process_id` | Unique ID of the process holding the lock |

The magic happens in three steps:

1. **Acquire** → Before running any SQL, Jetbase tries to set `is_locked = true`
2. **Run** → If successful, migrations proceed
3. **Release** → When done (success or failure), the lock is released

If the lock is already held? Jetbase immediately fails with a helpful message instead of waiting forever.

## Checking Lock Status

Curious if something's holding the lock?

```bash
jetbase lock-status
```

**When unlocked** (normal state):
```
Status: UNLOCKED
```

**When locked** (migration in progress):
```
Status: LOCKED
Locked At: 2025-12-25 14:30:22.123456
```

## Releasing a Stuck Lock

Sometimes things go wrong—a process crashes mid-migration, your laptop dies, or the connection drops. The lock stays acquired even though nothing is running.

If you're **100% sure** no migration is actually running:

```bash
jetbase unlock
```

Output:
```
Unlock successful.
```

!!! danger "Be Careful!"
    Only use `unlock` when you're absolutely certain no migration is in progress. Unlocking while a migration is actually running can corrupt your database.

```


### 🔄 Concurrent Deploys

```bash
# Server 1
jetbase upgrade  # Acquires lock, runs migrations...

# Server 2 (at the same time)
jetbase upgrade  # Fails immediately with "Lock is already held"
```

Server 2 gets a clear error. No corruption, no race conditions.


## Lock Commands Reference

| Command | What It Does |
|---------|--------------|
| `jetbase lock-status` | Check if database is locked |
| `jetbase unlock` | Force-release the lock |



