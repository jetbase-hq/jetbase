# jetbase fix

Repair migration files and checksums in one command.

## Usage

```bash
jetbase fix
```

## Description

The `fix` command is a convenience command that repairs both file issues and checksum issues. It's equivalent to running:

```bash
jetbase validate-files --fix
jetbase validate-checksums --fix
```

Use this when you want to quickly resolve migration drift without running multiple commands.


For detailed explanations of what each validation does and when to use `--fix`, see:

- [`validate-files`](validate-files.md) — Fix missing migration files or database history
- [`validate-checksums`](validate-checksums.md) — Fix modified or out-of-sync migration file checksums

> 
> See the [Validations Overview](../validations/index.md) for a comprehensive guide to every validation check Jetbase performs with `jetbase fix`.



