# Writing Migrations 📝

This guide covers everything you need to know about writing effective migration files in Jetbase.

## File Structure

Every migration file should have two sections:

```sql
-- upgrade
-- SQL statements to apply the migration

-- rollback
-- SQL statements to undo the migration
```

### Example: Creating a Table

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rollback
DROP TABLE IF EXISTS users;
```

## The `-- upgrade` Section

This section contains SQL that runs when you execute `jetbase upgrade`. It should contain all the statements needed to move your database forward.

### Multiple Statements

You can include multiple statements:

```sql
-- upgrade
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);

ALTER TABLE orders
ADD CONSTRAINT fk_orders_user
FOREIGN KEY (user_id) REFERENCES users(id);

-- rollback
DROP TABLE IF EXISTS orders;
```

## The `-- rollback` Section

This section contains SQL that runs when you execute `jetbase rollback`. It should completely undo everything in the upgrade section.

### Rollback Best Practices

1. **Drop in reverse order** — Drop foreign keys before tables
2. **Use `IF EXISTS`** — Makes rollbacks safer
3. **Consider data loss** — Some operations can't be undone with data intact

```sql
-- upgrade
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
UPDATE users SET phone = 'unknown' WHERE phone IS NULL;
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- rollback
ALTER TABLE users DROP COLUMN phone;
```

!!! warning "Data Loss"
The rollback above will lose all phone number data. This is often unavoidable, but make sure you understand the implications.

## Writing Good Migrations

### One Change Per Migration

Keep migrations focused on a single logical change:

✅ **Good:**

```
V20251225.143022__create_users_table.sql
V20251225.143023__create_orders_table.sql
V20251225.143024__add_foreign_keys.sql
```

❌ **Avoid:**

```
V20251225.143022__create_everything.sql
```

### Use Descriptive Names

Your migration description becomes part of the filename:

```bash
jetbase new "create users table"
# Creates: V20251225.143022__create_users_table.sql

jetbase new "add email verification fields to users"
# Creates: V20251225.143023__add_email_verification_fields_to_users.sql
```

### Handle NULL Values

When adding NOT NULL columns:

```sql
-- upgrade
-- Add column as nullable first
ALTER TABLE users ADD COLUMN status VARCHAR(20);

-- Set default values for existing rows
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Now make it NOT NULL
ALTER TABLE users ALTER COLUMN status SET NOT NULL;

-- rollback
ALTER TABLE users DROP COLUMN status;
```

### Use Transactions (PostgreSQL)

PostgreSQL supports transactional DDL, meaning if one statement fails, all statements in the migration are rolled back automatically.

## Common Patterns

### Creating Tables

```sql
-- upgrade
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rollback
DROP TABLE IF EXISTS products;
```

### Adding Columns

```sql
-- upgrade
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;

-- rollback
ALTER TABLE users DROP COLUMN login_count;
ALTER TABLE users DROP COLUMN last_login;
```

### Creating Indexes

```sql
-- upgrade
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- rollback
DROP INDEX IF EXISTS idx_orders_created_at;
DROP INDEX IF EXISTS idx_users_email;
```

### Adding Foreign Keys

```sql
-- upgrade
ALTER TABLE orders
ADD CONSTRAINT fk_orders_user
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE;

-- rollback
ALTER TABLE orders DROP CONSTRAINT fk_orders_user;
```

### Renaming Columns

```sql
-- upgrade
ALTER TABLE users RENAME COLUMN name TO full_name;

-- rollback
ALTER TABLE users RENAME COLUMN full_name TO name;
```

### Changing Column Types

```sql
-- upgrade
ALTER TABLE products ALTER COLUMN price TYPE DECIMAL(12,4);

-- rollback
ALTER TABLE products ALTER COLUMN price TYPE DECIMAL(10,2);
```

## Dangerous Operations

Some operations need extra care:

### Dropping Tables

```sql
-- upgrade
DROP TABLE IF EXISTS legacy_sessions;

-- rollback
-- ⚠️ Cannot restore data!
-- You would need to recreate the table structure
CREATE TABLE legacy_sessions (...);
```

### Removing Columns

```sql
-- upgrade
ALTER TABLE users DROP COLUMN middle_name;

-- rollback
-- ⚠️ Data is lost!
ALTER TABLE users ADD COLUMN middle_name VARCHAR(50);
```

### Truncating Data

```sql
-- upgrade
TRUNCATE TABLE logs;

-- rollback
-- ⚠️ Data cannot be restored!
-- Consider: Do you really need to truncate?
```

## Tips and Tricks

### Comments in SQL

Add comments to explain complex logic:

```sql
-- upgrade
-- Adding email verification flow
-- Users will need to verify their email before accessing premium features
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(100);
ALTER TABLE users ADD COLUMN verification_sent_at TIMESTAMP;

-- rollback
ALTER TABLE users DROP COLUMN verification_sent_at;
ALTER TABLE users DROP COLUMN verification_token;
ALTER TABLE users DROP COLUMN email_verified;
```

### Testing Migrations

Always test migrations locally:

```bash
# Apply migration
jetbase upgrade

# Test your application

# If something's wrong, roll back
jetbase rollback

# Fix the SQL and try again
```

### Dry Run First

Preview before applying:

```bash
jetbase upgrade --dry-run
```

## Next Steps

- [Migration Types](migration-types.md) — Learn about versioned and repeatable migrations
- [`upgrade` Command](../commands/upgrade.md) — Apply your migrations
- [`rollback` Command](../commands/rollback.md) — Undo migrations when needed
