# jetbase status

Displays which migrations have been applied and which migrations are pending.

## Usage

```bash
jetbase status
```

## Description

The `status` command gives you a clear overview of your migration state, showing both applied migrations and pending ones.


### Basic Usage

```bash
jetbase status
```

### Typical Output

```
                    Migrations Applied
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 20251220.100000   │ create_users_table                   │
│ 20251221.093000   │ add_email_to_users                   │
│ 20251222.140000   │ create_orders_table                  │
└───────────────────┴──────────────────────────────────────┘

                    Migrations Pending
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 20251223.110000   │ add_products_table                   │
│ 20251224.090000   │ add_shipping_info                    │
└───────────────────┴──────────────────────────────────────┘
```

### When Everything Is Up to Date

```
                    Migrations Applied
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 20251220.100000   │ create_users_table                   │
│ 20251221.093000   │ add_email_to_users                   │
└───────────────────┴──────────────────────────────────────┘

                    Migrations Pending
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│                                                          │
└───────────────────┴──────────────────────────────────────┘
```

### Fresh Database (No Migrations Applied)

```
                    Migrations Applied
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│                                                          │
└───────────────────┴──────────────────────────────────────┘

                    Migrations Pending
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 20251220.100000   │ create_users_table                   │
│ 20251221.093000   │ add_email_to_users                   │
└───────────────────┴──────────────────────────────────────┘
```

## Migration Type Indicators

The status command shows different prefixes for migration types:

| Prefix            | Meaning                        |
| ----------------- | ------------------------------ |
| `20251225.143022` | Versioned migration (standard) |
| `RUNS_ALWAYS`            | Runs Always migration    |
| `RUNS_ON_CHANGE`           | Runs On Change migration |


Example:
```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Version           ┃ Description                  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 20251225.143022   │ create_users_table           │
│ 20251225.144500   │ add_email_to_users           │
│ 20251225.150000   │ create_orders_table          │
│ RUNS_ALWAYS       │ refresh_materialized_views   │ 
│ RUNS_ON_CHANGE    │ stored_procedures            │
└───────────────────┴──────────────────────────────┘
```


## Notes

- Must be run from inside the `jetbase/` directory
- Compares files in `migrations/` with database records

