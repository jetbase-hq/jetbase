# jetbase current

Show the latest applied migration version.

## Usage

```bash
jetbase current
```

## Description

The `current` command displays the version number of the most recently applied migration. It's a quick way to check where your database schema currently stands.

## Output

### When Migrations Have Been Applied

```bash
jetbase current
```

Output:

```
Latest migration version: 20251225.143022
```

### When No Migrations Have Been Applied

```bash
jetbase current
```

Output:

```
No migrations have been applied yet.
```

## Notes

- Must be run from inside the `jetbase/` directory
- Shows only the version of the latest **versioned** migration
