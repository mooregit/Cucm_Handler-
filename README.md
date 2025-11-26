# Cucm_Handler-
A Python Interface for Cisco Unified Communications Manager (CUCM)

This repository provides a set of lightweight clients, service wrappers, and FastAPI REST endpoints for interacting with CUCM's SOAP-based management interfaces:

- AXL (AXL SOAP API) — configuration-level CRUD and introspection
- RIS (RISPort SOAP) — real-time device registration and status
- PerfMon (PerfMon SOAP) — node-level counters and performance metrics

The project contains reusable clients that wrap the raw Zeep SOAP client, higher-level service functions that implement helpful common operations (users, phones, lines, trunks, health), and a set of FastAPI routers which expose select functionality over REST.

---

## What's included ✅

- app/axl/
	- `axl_client.py` — generic dynamic Zeep-based AXL client with call(), list_operations(), and auto-generated methods for SOAP ops
	- `axl_service.py` — higher-level helpers for users, phones, lines, SIP trunk summaries, SQL helpers, and cluster/config summaries

- app/ris/
	- `ris_client.py` — generic RISPort SOAP client wrapper
	- `ris_service.py` — helpers to fetch registered devices and trunk status summaries

- app/perfmon/
	- `perfmon_client.py` — generic PerfMon SOAP client wrapper
	- `perfmon_service.py` — helpers to collect counters and produce basic health summaries

- app/core/
	- `ris_loader.py` / `perfmon_loader.py` — environment-based factory functions for clients (cached) and some config defaults
	- `axl_loader.py` — (placeholder) should provide `get_axl_client()` factory; router code depends on it

- app/api/
	- `router_axl_raw.py` — raw AXL introspection + proxy endpoints (list operations, operation signature, and dynamic call)
	- `router_status.py` — cluster status endpoints that combine AXL, RIS, and PerfMon data
	- Stubs: `router_devices.py`, `router_health.py`, `router_perfmon_raw.py`, `router_ris_raw.py`, `router_users.py`

---

## Features / Highlights 💡

- AXL dynamic client: loads the WSDL and exposes every SOAP operation as a native method (e.g. `axl.getUser(...)`) while still supporting a `call(operation, **params)` for dynamic calls.
- FastAPI endpoints to inspect and call AXL operations directly (`/axl/operations`, `/axl/operations/{name}`, `POST /axl/{operation}`)
- Cluster-wide status endpoint (`/status/cluster`) combining configuration (AXL), real-time registration (RIS), and performance metrics (PerfMon)
- Convenience service wrappers (users, phones, lines, SIP trunk summaries, SQL helpers)
- Performance counters collection for basic health checks of CUCM nodes

---

## Requirements & Installation 🔧

Install the required Python packages:

```bash
python3 -m pip install fastapi uvicorn zeep requests pydantic
```

If you prefer, add a `requirements.txt` with these dependencies so tooling can install them: (this repo currently does not include a populated list)

---

## Configuration / Environment variables ⚙️

The code loads configuration from environment variables. The key variables used by the client loader functions are:

- `CUCM_HOST` — CUCM Publisher hostname or IP (required)
- `CUCM_USERNAME` — Default AXL/RIS/PerfMon username (optional if service-specific ones are set)
- `CUCM_PASSWORD` — Default AXL/RIS/PerfMon password (optional if service-specific ones are set)
- `CUCM_VERIFY_SSL` — Whether to verify TLS certs (defaults to `false`)

- AXL-specific:
	- `CUCM_AXL_WSDL` — Path to AXL WSDL (optional; project includes `app/axl/schema` as convention)
	- `CUCM_AXL_USERNAME`, `CUCM_AXL_PASSWORD` — Override AXL credentials (optional)

- RIS-specific:
	- `CUCM_RIS_WSDL` — Path to RIS WSDL (default: `app/ris/schema/RISService70.wsdl`)
	- `CUCM_RIS_USERNAME`, `CUCM_RIS_PASSWORD` — RIS-specific credentials (or `CUCM_USERNAME`/`CUCM_PASSWORD`)

- PerfMon-specific:
	- `CUCM_PERFMON_WSDL` — Path to PerfMon WSDL (default: `app/perfmon/schema/PerfmonService.wsdl`)
	- `CUCM_PERFMON_USERNAME`, `CUCM_PERFMON_PASSWORD` — PerfMon-specific credentials (or `CUCM_USERNAME`/`CUCM_PASSWORD`)

Note: The repo contains loader helpers (`app/core/ris_loader.py`, `app/core/perfmon_loader.py`) that read these environment variables and return a configured client object.

---

## Running the API (example) ▶️

The repo includes API routers but does not ship a complete `app/main.py` for wiring the `FastAPI` application. You can create a minimal `main.py` to run the server:

```python
from fastapi import FastAPI
from app.api import router_axl_raw, router_status

app = FastAPI(title="Cucm_Handler API")
app.include_router(router_axl_raw.router, prefix="/axl")
app.include_router(router_status.router)

```

Run with Uvicorn:

```bash
export CUCM_HOST=your.cucm
export CUCM_USERNAME=axl-user
export CUCM_PASSWORD=secret
export CUCM_VERIFY_SSL=false
python -m uvicorn app.main:app --reload --port 8000
```

Quick examples:

- List AXL operations:
```bash
curl http://localhost:8000/axl/operations
```
- Get signature for operation `getUser`:
```bash
curl http://localhost:8000/axl/operations/getUser
```
- Call an AXL operation (raw proxy):
```bash
curl -X POST http://localhost:8000/axl/getUser -H 'Content-Type: application/json' \
	-d '{"params": {"userid":"jdoe"}}'
```
- Get a cluster status summary:
```bash
curl http://localhost:8000/status/cluster
```

---

## API Endpoints (current) 📡

- `GET /axl/operations` — list available AXL SOAP operations
- `GET /axl/operations/{name}` — get the signature for a specific AXL operation
- `POST /axl/{operation}` — proxy a raw AXL operation (JSON body with `params` dict)
- `GET /status/cluster` — combined AXL+RIS+PerfMon cluster health summary
- `GET /status/nodes` — list CUCM process nodes from AXL
- `GET /status/devices` — RIS get registered phones and trunks (counts + sample)
- `GET /status/perfmon` — PerfMon health summary per node

Planned or stubbed routers in `app/api`:
- `router_users.py`, `router_devices.py`, `router_perfmon_raw.py`, `router_ris_raw.py`, `router_health.py` — intended to expose more CRUD operations and raw endpoints; some are currently empty and awaiting implementation.

---

## Notes & Best Practices ⚠️

- WSDL files: Cisco WSDLs are required for the Zeep clients (AXL, RIS, PerfMon). These are usually included in Cisco public docs or collected from a lab. The loader functions default to local paths under `app/*/schema` but you can override with environment vars.
- Certificates: In many lab environments, CUCM uses self-signed certs; set `CUCM_VERIFY_SSL=false` unless you have proper CA certs configured.
- Credentials: Use service accounts with limited permissions (AXL read-only or restricted to the needed operations).
- The repo aims to be a lightweight bridge between SOAP and REST; always validate any user inputs that may be forwarded to SQL endpoints.

---

## Contributing & Development 🛠️

If you'd like to contribute, please consider:

- Implementing the missing router modules and wire them into `app.main`.
- Adding unit tests and CI (pytest, linting).
- Add a populated `requirements.txt` or `pyproject.toml` for reproducible environments.

---

## License

MIT-style (or your preferred license). Please update the LICENSE file as appropriate.

---

If you'd like, I can also:
- Add a ready-to-run `app/main.py` that wires the routers up and add a sample `requirements.txt`.
- Create README badges, quick start script, or minimal tests.

Let me know if you'd like any of these next steps.

---

## Database Models (SQLAlchemy) 🗄️

This project includes SQLAlchemy models designed to hold a multi-tenant inventory of unified communications infrastructure and periodic health snapshots. These are a starting point for integrating a database-backed inventory, health checks, and configuration management.

You can find the models under `app/models/` and the notable ones are:

- `tenant.py` — multi-tenant container for server groups and metadata
- `cucm_server.py` — CUCM server model with identity, version, AXL connectivity, and health snapshot fields
- `uc_base.py` — an abstract base for UC servers (shared fields)
- `expressway_server.py`, `imp_server.py`, `ucce_server.py`, `uccx_server.py`, `unity_connection_server.py` — vendor-specific server models
- `cube_gateway.py`, `cms_server.py`, `cer_server.py` — gateway and monitoring servers

These models use the PostgreSQL dialect for UUID and INET types and are structured for production usage. If you plan to persist this data, you should add migration tooling (Alembic) and a proper database connection layer.

---

## Development Notes & Next Steps ⚙️

- Add `alembic` configuration and migrations to manage database versions and schema changes.
- Populate `app/schemas/` with Pydantic models for request/response validation used by the API endpoints.
- Implement `app/core/axl_loader.py` to mirror `ris_loader.py` and `perfmon_loader.py`, providing `get_axl_client()`.
- Implement or wire `app/main.py` to create and register the FastAPI app and routers — a starter `main.py` snippet is included earlier in this README.
- Populate `app/wsdl/`, `app/*/schema/` with the required WSDLs for the AXL, RIS, and PerfMon clients or document how to provide custom paths using environment variables.
- Add example `.env.example` for local development values.

If you'd like, I can implement one or more of these items now — tell me which and I'll proceed.
