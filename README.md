# Radha ERP Monorepo

This repository contains the services and utilities that compose Radha ERP.

## Prerequisites

The startup script requires Python 3 with the `python3-venv` package as well as Node.js and npm.
On Debian based systems you can install them with:
```bash
sudo apt install python3 python3-venv nodejs npm
```


## Scripts

- **start_radha_erp.sh** – starts all backend and frontend services. When executed for the first time it will create the required Python virtual environments and install dependencies automatically if they are missing.
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

## Troubleshooting

If the browser only shows a loading message and the application does not open,
check whether the backend services are running correctly. The
`start_radha_erp.sh` script saves logs for each service inside the `logs`
directory. Inspect `logs/startup_main.log` and the individual service logs for
errors, ensuring that ports 8010, 8015 and 8020 are not in use by other
processes.
