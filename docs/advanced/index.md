# Advanced Topics

## Migration Types

Jetbase supports three types of migrations: **Versioned**, **Runs Always**, and **Runs On Change**. Versioned migrations cover most use cases, but the repeatable types are useful for specialized cases.

→ [Learn about Migration Types](migration-types.md)

## Migration Locking

Jetbase automatically locks the database during migrations to prevent conflicts when multiple processes try to migrate simultaneously.

→ [Learn about Locking](migration-locking.md)
