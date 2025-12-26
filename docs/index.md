# Welcome to Jetbase 🚀

**Jetbase** is a friendly, lightweight database migration tool for Python projects. Think of it as your database's best friend — helping you keep track of changes, roll them back when needed, and always know exactly where you stand.

## What is Jetbase?

Jetbase helps you manage database schema changes (migrations) in a simple, version-controlled way. Whether you're adding a new table, modifying columns, or need to undo a change, Jetbase has got your back!

### Key Features ✨

- **📦 Simple Setup** — Get started with just one command
- **⬆️ Easy Upgrades** — Apply pending migrations with confidence
- **⬇️ Safe Rollbacks** — Made a mistake? No problem, roll it back!
- **📊 Clear Status** — Always know which migrations have been applied
- **🔒 Migration Locking** — Prevents conflicts when multiple processes try to migrate
- **✅ Checksum Validation** — Detects if migration files have been modified
- **🔄 Repeatable Migrations** — Support for migrations that run on every upgrade

## Quick Start 🏃‍♂️

### Installation

```bash
pip install jetbase
```

### Initialize Your Project

```bash
jetbase init
cd jetbase
```

This creates a `jetbase/` directory with:

- A `migrations/` folder for your SQL files
- An `env.py` configuration file

### Configure Your Database

Edit `jetbase/env.py` with your database connection string:

```python
sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
```

### Create Your First Migration

```bash
jetbase new "create users table"
```

This creates a new SQL file like `V20251225.120000__create_users_table.sql`.

### Write Your Migration

Open the newly created file and add your SQL:

```sql
-- upgrade
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- rollback
DROP TABLE users;
```

### Apply the Migration

```bash
jetbase upgrade
```

That's it! Your database is now up to date. 🎉

## Next Steps

- 📖 [Getting Started Guide](getting-started.md) — More detailed setup instructions
- 🛠️ [Commands Reference](commands/index.md) — Learn all available commands
- 📝 [Writing Migrations](migrations/writing-migrations.md) — Best practices for migration files
- ⚙️ [Configuration](configuration.md) — Customize Jetbase for your needs

## Supported Databases

Jetbase currently supports:

- ✅ PostgreSQL
- ✅ SQLite

## Need Help?

Check out the [troubleshooting guide](troubleshooting.md) or open an issue on GitHub!
