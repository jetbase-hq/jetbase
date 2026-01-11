# jetbase init

Initialize Jetbase in your current directory.

## Usage

```bash
jetbase init
```

## Description

The `init` command sets up Jetbase in your project by creating the necessary directory structure and configuration files. This is typically the first command you run when setting up Jetbase for a new project.

## What It Creates

Running `jetbase init` creates a `jetbase/` directory with:

```
jetbase/
├── migrations/     # Directory for your SQL migration files
└── env.py          # Configuration file for database connection
```

### The `env.py` File

The generated configuration file looks like this:

```python
# Jetbase Configuration
# Update the sqlalchemy_url with your database connection string.

sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
```

!!! important
After running `init`, you need to update the `sqlalchemy_url` in `env.py` with your actual database connection string.

> **Next Step:**  
> After running `jetbase init`, move into the `jetbase` directory with:
> 
> ```bash
> cd jetbase
> ```
> 
> **Important:**  
> All future `jetbase` commands should be run *inside* the `jetbase` directory.

## Examples

### Basic Usage

```bash
# In your project root
jetbase init
```

Output:

```
Initialized Jetbase project in /path/to/your/project/jetbase
Run 'cd jetbase' to get started!
```

### Complete Workflow

```bash
# 1. Initialize Jetbase
jetbase init

# 2. Move into the jetbase directory
cd jetbase

# 3. Edit env.py with your database URL
# (use your favorite editor)

# 4. Create your first migration
jetbase new "create users table" -v 1

# 5. Apply migrations
jetbase upgrade
```

## Notes

- All other Jetbase commands must be run from inside the `jetbase/` directory.
- The `migrations/` directory will be empty after initialization. Use `jetbase new` to create your first migration, (or create migration files manually. See [Migrations Overview](../migrations/index.md)).

