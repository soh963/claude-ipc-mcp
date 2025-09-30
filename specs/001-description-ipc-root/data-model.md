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
- session_token: string (optional; present when broker requires session auth)

### Session
- instance_id: string
- session_token: string
- path: string (filesystem location)
- default_link: boolean (true if also written to legacy `%USERPROFILE%\\.ipc-session`)

### MessageStatus
- message_id: string (uuid)
- status: enum[queued, delivered, ack, answered, error]
- updated_at: datetime
- error_reason: string (optional)

### ResponderPolicy
- name: enum[simple, smart]
- description: string

## Relationships
- Broker 1 - N ProjectIPCContext (connections)
- ProjectIPCContext 1 - N Responder
- Message references 2 addresses (from, to)
- Session belongs to an instance and is stored under the user's home directory

## Validation Rules
- secret must exist for any outbound connection
- version compatibility: major equal, minor within ±1
- project_id stable across runs
- session_token must be non-empty when session auth is enabled
- correlation IDs (corr_id) are unique per project during their lifetime
- clearing messages must not delete audit logs; admin actions are append-only audited

## Operations
- send_message(project_id, from, to, payload, corr_id?) -> message_id
- receive_messages(project_id, to, since_ts?) -> [Message]
- ack_message(message_id) -> ok
- await_answer(corr_id, timeout) -> Message | Timeout
- clear_messages(project_id) -> { deleted_inbox, deleted_outbox }
- reset_instances(project_id) -> { removed }
- delete_instance(project_id, instance_id) -> { removed }
- register_instance(project_id, instance_id) -> session_token
- unregister_instance(project_id, instance_id) -> ok
- start_responder(project_id, instance_id, policy) -> pid
- stop_responder(project_id, instance_id) -> stopped
