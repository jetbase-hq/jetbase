# jetbase unlock

Manually release the migration lock.

## Usage

```bash
jetbase unlock
```

## Description

The `unlock` command forcefully releases the migration lock, allowing migrations to run again. This should only be used when you're certain that no migration is currently in progress.

!!! danger "Use With Caution"
Only use this command when you're absolutely certain no migration process is running.

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


## See Also

- [`lock-status`](lock-status.md) — Check if the database is locked
- [`upgrade`](upgrade.md) — Run migrations
- [Troubleshooting](../troubleshooting.md) — Common issues and solutions
