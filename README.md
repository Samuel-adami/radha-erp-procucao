# Radha ERP Monorepo

This repository contains the services and utilities that compose Radha ERP.

## Prerequisites

On Debian based systems you can install them with:
```bash
sudo apt install python3 python3-venv nodejs npm
```


## Scripts

- **update_github.sh** – commits and pushes local changes to GitHub.

The script uses the environment variable `RADHA_ERP_ROOT` to locate the
monorepo. When the variable is not set, it tries to detect the current
repository location automatically using `git`. Normally you can run the
the script without setting anything when executing it inside the repository.

Example usage specifying a custom path:

```bash
RADHA_ERP_ROOT=/opt/radha/radha-erp ./update_github.sh
```

## Running the services
See `rodar_ambientes.txt` for the commands used to launch each backend and the frontend. You can adapt these into a systemd unit like the example `radha-erp.service` provided in the repository.
The `start_services.sh` script offers a simple way to run every component locally.

### Default credentials
When the application is started for the first time and the user database is empty,
it will create a default administrator account. You can override the username and
password using the `RADHA_ADMIN_USER` and `RADHA_ADMIN_PASS` environment
variables. The default values are `admin` / `admin`.


## Troubleshooting

If the browser only shows a loading message and the application does not open,
check whether the backend services are running correctly. The
directory. Inspect `logs/startup_main.log` and the individual service logs for
errors, ensuring that ports 8010, 8015 and 8020 are not in use by other
processes.
