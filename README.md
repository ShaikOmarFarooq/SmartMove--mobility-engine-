# SmartMove – Core Engine

SmartMove is the backend engine of a shared-mobility. It manages a fleet of
10,000 bikes, e-scooters and mopeds across London, Milan and Rome, applies
city-specific rules, processes asynchronous telemetry, and keeps a tamper-evident
audit trail. A small web frontend lets you inspect and operate the system.

No external database or high-level framework is used: all data is persisted in local
JSON files and the web server uses only the Python standard library.

## Features

- **Vehicle state machine** – `available`, `reserved`, `in_use`, `maintenance`,
  `emergency_lock`, `relocating`, with validated transitions.
- **Multi-city rules**
  - London: £5 congestion charge added to the final bill.
  - Milan: helmet presence check before unlocking.
  - Rome: restricted zone (latitude > 41.9) triggers a lock and ends the rental.
- **Telemetry processing** – GPS, battery and temperature streamed per vehicle.
  - Temperature > 60 °C → emergency lock and rental termination.
  - Battery < 5 % → rental termination and move to maintenance.
  - Movement without an active rental → emergency lock (theft alarm).
- **Concurrency** – per-vehicle locks, an event bus with a processor thread, and
  telemetry worker threads, so telemetry updates and rentals do not clash.
- **Audit trail** – append-only `data/audit.log` with sequential IDs and a checksum
  chained to the previous entry; `verify_integrity()` detects tampering.
- **Web frontend** – dashboard, vehicle browser, rental management, audit viewer and
  simulation control.

## Requirements

- Python 3.9 or newer
- Nothing to install to run the app or the frontend
- `pytest` and `coverage` only for the tests (`pip install -r requirements.txt`)

## Quick start (web frontend)

Run from the **project root** (the folder containing `data/` and `smartmove/`),
because data files are located with relative paths.

```bash
python smartmove/web/server.py
```

Then open <http://localhost:8000>.

Options:

| Option       | Description                                        |
|--------------|----------------------------------------------------|
| `--simulate` | Start telemetry and rental simulation immediately  |
| `--port N`   | Use another port (default 8000)                    |
| `--host H`   | Bind address (default 127.0.0.1)                   |

Stop with `Ctrl+C`. On some systems use `python3`, or `py` on Windows.

> Rentals started from the page write to `data/audit.log`. Back the file up first if
> you want to keep the original log.

### What the frontend offers

- **Dashboard** – fleet counts by state, city and type; active rentals; battery stats.
- **Vehicles** – filter by city, type, state or ID; open a vehicle to unlock it for a
  user or end its rental.
- **Rentals** – live list of active rentals with duration and running cost.
- **Audit log** – latest entries with checksums, vehicle filter and a
  **Verify integrity** button.
- **Simulation** – header button to start/stop the telemetry and rental simulation.

## Running the simulation without the frontend

```bash
# Linux / macOS
PYTHONPATH=smartmove python smartmove/main.py

# Windows PowerShell
$env:PYTHONPATH="smartmove"; python smartmove/main.py
```

Press `Ctrl+C` for a graceful shutdown.

## Running the tests

```bash
pip install -r requirements.txt
PYTHONPATH=smartmove pytest
```

With coverage (as used for SonarQube):

```bash
PYTHONPATH=smartmove coverage run --source=smartmove -m pytest
coverage xml -o coverage.xml
```

Or with Docker: `docker compose up app` (SonarQube and scanner services are also
defined in `docker-compose.yml`).

## Project structure

```
data/
  vehicles.json         persisted fleet
  users.json            persisted users
  audit.log             append-only, checksum-chained audit trail
smartmove/
  main.py               headless entry point (simulation)
  core/
    controller.py       SmartMoveCentralController (facade)
    state_machine.py    valid vehicle state transitions
    pricing.py          per-minute pricing (0.25 / min)
    event_bus.py, event_processor.py, events.py
    services/
      rental_service.py     start/end/terminate rentals, city rules
      telemetry_service.py  telemetry-driven safety logic
  domain/               Vehicle, User, Rental, enums, telemetry types
  rules/                London, Milan and Rome city rules
  persistence/
    storage.py          atomic JSON load/save
    audit_log.py        thread-safe audit log with checksum chain
  simulation/           fleet/user/telemetry factories, workers, rental simulator
  web/
    server.py           stdlib HTTP server + JSON API
    static/index.html   single-page frontend
tests/                  pytest suite
```

## Architecture overview

```
 Rental simulator ─┐                          ┌─> RentalService ───┐
                   ├─> EventBus ─> EventProcessor                  ├─> AuditLog
 Telemetry workers ┘                          └─> TelemetryService ┘
                                   ▲
 Web frontend ──> HTTP API ────────┘ (calls the controller directly)
```

Producers (simulators and the web API) never modify vehicles unprotected: every state
change happens while holding the vehicle's own lock.

## Web API

All responses are JSON. Errors return `{"error": "..."}` with status 404 (not found),
409 (business rule violated, e.g. vehicle unavailable or helmet missing) or 400.

| Method | Path                     | Description                                   |
|--------|--------------------------|-----------------------------------------------|
| GET    | `/api/summary`           | Fleet statistics                              |
| GET    | `/api/vehicles`          | List; query: `city`, `state`, `type`, `q`, `limit`, `offset` |
| GET    | `/api/vehicles/<id>`     | Vehicle details and active rental             |
| GET    | `/api/users`             | List users; query: `q`, `limit`               |
| GET    | `/api/rentals`           | Active rentals                                |
| GET    | `/api/audit`             | Latest entries; query: `limit`, `entity`      |
| GET    | `/api/audit/verify`      | Verify the checksum chain                     |
| POST   | `/api/rentals/start`     | Body: `{"user_id", "vehicle_id"}`             |
| POST   | `/api/rentals/end`       | Body: `{"vehicle_id"}`                        |
| POST   | `/api/simulation`        | Body: `{"running": true/false}`               |

## Troubleshooting

- **`ModuleNotFoundError`** – run the command from the project root.
- **Port already in use** – start with `--port 9000`.
- **Slow first start** – loading and initialising 10,000 vehicles takes a few seconds.
