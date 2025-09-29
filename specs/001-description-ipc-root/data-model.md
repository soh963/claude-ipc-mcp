# Data Model: Global IPC CLI

## Entities

### Broker (Singleton)
- id: string (implicit: singleton)
- version: semver
- port: int
- started_at: datetime
- status: enum[running, stopped]

### ProjectIPCContext
- project_id: string (stable)
- root_path: string
- secret: string (stored in .ipc/secrets.env)
- config_path: string (.ipc/config.yaml)
- state_path: string (.ipc/state/)
- logs_path: string (.ipc/logs/)
- responders: array[ResponderRef]

### Responder
- name: string
- role: string
- topics: array[string]
- registered_at: datetime
- status: enum[active, stopped]

### Identity & Routing
- address: string (project_id:name or role/topic based)
- handshake: object { project_id, secret_hash, version }

### Message
- id: string (uuid)
- from: string (address)
- to: string (address)
- topic: string
- payload: object
- ts: datetime
- corr_id: string (optional)

## Relationships
- Broker 1 - N ProjectIPCContext (connections)
- ProjectIPCContext 1 - N Responder
- Message references 2 addresses (from, to)

## Validation Rules
- secret must exist for any outbound connection
- version compatibility: major equal, minor within ±1
- project_id stable across runs
