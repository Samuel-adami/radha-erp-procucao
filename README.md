# Radha ERP Monorepo

This repository contains the services and utilities that compose Radha ERP.

## Scripts

- **start_radha_erp.sh** – starts all backend and frontend services.
- **update_github.sh** – commits and pushes local changes to GitHub.

Both scripts use the environment variable `RADHA_ERP_ROOT` to locate the
monorepo. When the variable is not set, they try to detect the current
repository location automatically using `git`. Normally you can run the
scripts without setting anything when executing them inside the repository.

Example usage specifying a custom path:

```bash
RADHA_ERP_ROOT=/opt/radha/radha-erp ./start_radha_erp.sh
RADHA_ERP_ROOT=/opt/radha/radha-erp ./update_github.sh
```
