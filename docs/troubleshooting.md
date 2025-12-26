# Troubleshooting 🔧

Having issues with Jetbase? This guide covers common problems and their solutions.

## Common Issues

### "Jetbase directory not found"

**Problem:** You see an error about the jetbase directory not being found.

**Cause:** You're running commands from the wrong directory.

**Solution:** Make sure you're inside the `jetbase/` directory:

```bash
cd jetbase
jetbase status
```

Or if you haven't initialized yet:

```bash
jetbase init
cd jetbase
```

---

### "Connection refused" or Database Connection Errors

**Problem:** Can't connect to the database.

**Cause:** Database server isn't running, or connection string is wrong.

**Solutions:**

1. **Check if database is running:**

   ```bash
   # PostgreSQL
   pg_isready -h localhost -p 5432

   # Or check service status
   brew services list  # macOS
   systemctl status postgresql  # Linux
   ```

2. **Verify connection string in `env.py`:**

   ```python
   # Format: postgresql://user:password@host:port/database
   sqlalchemy_url = "postgresql://postgres:mypassword@localhost:5432/mydb"
   ```

3. **Test connection manually:**
   ```bash
   psql postgresql://user:password@localhost:5432/database
   ```

---

### "Migration file not found" During Rollback

**Problem:** Can't rollback because migration file is missing.

**Cause:** The SQL file was deleted but the migration record exists in the database.

**Solutions:**

1. **Restore the file from version control:**

   ```bash
   git checkout -- migrations/V20251225.143022__missing_file.sql
   ```

2. **Or remove the database record:**
   ```bash
   jetbase fix
   ```

---

### "Database is locked"

**Problem:** Migrations won't run because the database is locked.

**Cause:** A previous migration process didn't release the lock (crashed or was killed).

**Solutions:**

1. **Check if a migration is actually running:**

   ```bash
   ps aux | grep jetbase
   jetbase lock-status
   ```

2. **If no migration is running, unlock:**
   ```bash
   jetbase unlock
   ```

!!! warning
Only unlock if you're **certain** no migration is running!

---

### Checksum Mismatch Errors

**Problem:** Upgrade fails with checksum validation errors.

**Cause:** A migration file was modified after it was applied.

**Solutions:**

1. **If the change was accidental, restore the original:**

   ```bash
   git checkout -- migrations/V20251225.143022__the_file.sql
   ```

2. **If the change was intentional, update the checksum:**

   ```bash
   jetbase validate-checksums --fix
   ```

3. **Skip validation (temporary fix):**
   ```bash
   jetbase upgrade --skip-checksum-validation
   ```

---

### "Permission denied" Errors

**Problem:** Database operations fail with permission errors.

**Cause:** Database user lacks necessary privileges.

**Solutions:**

1. **Grant necessary permissions:**

   ```sql
   -- PostgreSQL
   GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myuser;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myuser;
   ```

2. **Or use a superuser for migrations** (development only)

---

### Migrations Applied But Table Doesn't Exist

**Problem:** `jetbase status` shows migration as applied, but the table isn't there.

**Cause:** Migration was recorded but SQL failed, or table was manually dropped.

**Solutions:**

1. **Rollback and re-apply:**

   ```bash
   jetbase rollback
   jetbase upgrade
   ```

2. **If rollback fails, manually fix:**
   ```sql
   -- Remove the migration record
   DELETE FROM jetbase_migrations WHERE version = '20251225.143022';
   ```
   Then:
   ```bash
   jetbase upgrade
   ```

---

### "Cannot specify both 'count' and 'to-version'"

**Problem:** Error when running upgrade or rollback.

**Cause:** You used both `--count` and `--to-version` options together.

**Solution:** Use only one:

```bash
# Either specify count
jetbase upgrade --count 3

# Or specify version
jetbase upgrade --to-version 20251225.143022

# Not both
```

---

### Migrations Running Twice in CI/CD

**Problem:** Same migration runs multiple times in parallel CI jobs.

**Cause:** Multiple processes trying to migrate simultaneously.

**Solution:** The lock should prevent this, but ensure:

1. **Only one job runs migrations:**

   ```yaml
   # In your CI config, run migrations once
   deploy:
     steps:
       - run: cd jetbase && jetbase upgrade
   ```

2. **Use proper job dependencies to ensure migrations run first**

---

## Diagnostic Commands

### Check Current State

```bash
# Current version
jetbase current

# Full status
jetbase status

# Migration history
jetbase history
```

### Check for Issues

```bash
# Verify checksums
jetbase validate-checksums

# Check for missing files
jetbase validate-files

# Check lock status
jetbase lock-status
```

### Preview Changes

```bash
# See what would run
jetbase upgrade --dry-run

# See what would rollback
jetbase rollback --dry-run
```

## Database-Specific Issues

### PostgreSQL

**Issue:** `FATAL: role "username" does not exist`

```bash
# Create the user
createuser -s username

# Or in psql
CREATE USER username WITH PASSWORD 'password' SUPERUSER;
```

**Issue:** `FATAL: database "dbname" does not exist`

```bash
# Create the database
createdb dbname

# Or in psql
CREATE DATABASE dbname;
```

### SQLite

**Issue:** `unable to open database file`

Make sure the directory exists:

```bash
mkdir -p /path/to/database/directory
```

And use the correct path format:

```python
# Relative path
sqlalchemy_url = "sqlite:///mydb.sqlite"

# Absolute path (note: 4 slashes)
sqlalchemy_url = "sqlite:////home/user/data/mydb.sqlite"
```

## Getting More Help

### Enable Debug Output

Check what SQL is being executed:

```bash
jetbase upgrade --dry-run
```

### Check the Migration Files

Look at your migrations directory:

```bash
ls -la migrations/
```

### Verify Database State

Check the Jetbase tables directly:

```sql
-- See applied migrations
SELECT * FROM jetbase_migrations ORDER BY order_executed;

-- Check lock status
SELECT * FROM jetbase_lock;
```

## Still Stuck?

If you're still having issues:

1. Check the [GitHub Issues](https://github.com/jaz-alli/jetbase/issues) for similar problems
2. Open a new issue with:
   - Your Jetbase version
   - Python version
   - Database type and version
   - The error message
   - Steps to reproduce
