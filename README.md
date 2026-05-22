# InferFlow

**Intelligent conversation platform with streaming LLM responses, event-driven ingestion, and real-time monitoring.**

InferFlow is an async-first, event-driven platform for building production-grade conversational AI experiences. It separates inference, persistence, and monitoring into independent services connected via Redis Streams — enabling each component to scale, fail, and evolve independently.

## Core Capabilities

- **Streaming Chat** — Server-Sent Events (SSE) for real-time token-by-token LLM responses
- **Event-Driven Ingestion** — Fire-and-forget event publishing; inference never waits for persistence
- **Real-Time Monitoring** — WebSocket-based event fanout and metrics aggregation
- **Multi-Model Support** — Provider-agnostic LLM SDK for hot-swappable model routing (planned)
- **Horizontal Scalability** — Redis consumer groups enable independent worker scaling

---

## Architecture

```
┌─────────────┐     SSE Stream      ┌──────────────────┐
│             │ ◄────────────────── │                  │
│   Frontend  │                     │   Chat Service   │──── LLM Provider
│   (React)   │ ────────────────► │   (FastAPI)      │     (OpenAI, etc.)
│             │     HTTP POST       │                  │
└─────────────┘                     └────────┬─────────┘
                                             │
                                             │ XADD (fire-and-forget)
                                             ▼
                                    ┌──────────────────┐
                                    │                  │
                                    │  Redis Streams   │
                                    │  (Event Bus)     │
                                    │                  │
                                    └───────┬──┬───────┘
                                            │  │
                          ┌─────────────────┘  └─────────────────┐
                          │ XREADGROUP                           │ XREADGROUP
                          ▼                                      ▼
                 ┌──────────────────┐                   ┌──────────────────┐
                 │                  │                   │                  │
                 │ Ingestion Worker │                   │ Monitoring Svc   │
                 │ (Async Consumer) │                   │ (FastAPI + WS)   │
                 │                  │                   │                  │
                 └────────┬─────────┘                   └──────────────────┘
                          │                                      │
                          │ INSERT                               │ WebSocket
                          ▼                                      ▼
                 ┌──────────────────┐                   ┌──────────────────┐
                 │                  │                   │                  │
                 │   PostgreSQL     │                   │   Dashboard      │
                 │   (Data Store)   │                   │   (Future)       │
                 │                  │                   │                  │
                 └──────────────────┘                   └──────────────────┘
```

### Design Principles

- **Async-first**: Every service uses async I/O. No blocking calls in the hot path.
- **Event-driven**: Services communicate through events, not direct calls. This enables independent scaling and fault isolation.
- **Separation of concerns**: Inference, persistence, and monitoring are separate processes with distinct lifecycles.
- **Fire-and-forget publishing**: The chat service publishes events to Redis Streams without waiting for downstream processing. Users get responses faster.

---

## Service Responsibilities

| Service | Role | Protocol |
|---------|------|----------|
| **Frontend** | React SPA — chat interface, conversation management | HTTP, SSE |
| **Chat Service** | Conversation orchestration, LLM inference, SSE streaming | REST, SSE |
| **Ingestion Worker** | Consumes inference events, persists to PostgreSQL | Redis Streams consumer |
| **Monitoring Service** | Real-time event fanout, metrics aggregation | WebSocket, Redis Streams |
| **Redis** | Event bus (Streams), caching, session storage | TCP |
| **PostgreSQL** | Primary data store — conversations, messages, inference logs | TCP |

### Conversation Lifecycle & Architecture

The application uses an **in-memory repository abstraction** during this phase to decouple the business logic from the database layer. This ensures that the frontend and the core service logic are stable before introducing PostgreSQL.

1. **Repository Abstraction:** `ConversationRepository` abstracts data access. The `InMemoryConversationRepository` provides immediate state persistence, making it trivial to swap in a `PostgresConversationRepository` later without touching `ChatService` or the API layer.
2. **Conversation Management:** Conversations and their associated messages are managed through REST APIs (`POST /api/v1/conversations`, `GET /api/v1/conversations`, etc.).
4. **Deferred Persistence:** In this phase, persistence to PostgreSQL is intentionally deferred. Why? Because the hardest part of building LLM apps is nailing the streaming UX and decoupled event flow. Once the SSE stream and the Fire-and-Forget architecture are rock solid, adding the database layer becomes a standard engineering task.

### Telemetry SDK & Event-Driven Pipeline
The architecture leverages a decoupled observability pipeline. The `ChatService` wraps the provider via the `TelemetryWrapper`.

1. **Why wrapper-level telemetry?**: We separate generation from observability. The Gemini/OpenAI SDKs focus purely on streaming tokens. The `TelemetryWrapper` intercepts the stream to calculate `ttft_ms` (Time To First Token), generate `request_id`s, and manage the stream lifecycle.
2. **Fire-and-Forget Ingestion**: Telemetry is emitted to a Redis Stream (`llm.inference.events`) asynchronously. The `TelemetryProducer` uses a robust `try-except` structure: if Redis goes down, events are dropped, but **inference streaming to the user never breaks**.
3. **Normalized Event Contracts**: `packages/shared` defines standard event shapes like `InferenceStartedEvent`, `InferenceCompletedEvent`, etc., guaranteeing a uniform observability schema regardless of the underlying LLM provider.
4. **Replayability & Fanout**: By writing to Redis Streams before persisting to a database, we allow multiple consumers (analytics, ingestion workers, realtime monitoring) to consume these events at their own pace.

### Ingestion Pipeline (`apps/ingestion-worker/`)
A standalone async worker that consumes telemetry events from Redis Streams and durably persists them to PostgreSQL.

1. **Redis Consumer Groups**: The worker joins the `ingestion-group` consumer group on `llm.inference.events` using `XREADGROUP`. This enables horizontal scaling — multiple workers can share the workload without duplicating events. Unacknowledged messages are automatically redelivered.
2. **Pipeline Stages**: Each event flows through: `consume → validate → redact PII → persist → ACK`. Events are only ACK'd after successful DB persistence. Failed writes leave the message unACK'd for automatic redelivery.
3. **Idempotency**: The `inference_logs` table has a `UNIQUE` constraint on `request_id`. The repository uses `ON CONFLICT (request_id) DO NOTHING`, making the pipeline safe against Redis replays and duplicate delivery.
4. **PII Redaction**: Before persistence, error payloads are scanned for emails, phone numbers, and credit card patterns using regex-based redaction. This prevents accidental PII leakage from LLM error messages.
5. **Dead-Letter Stream**: Invalid events (malformed JSON, unknown event types, validation failures) are routed to `llm.inference.invalid` and ACK'd from the main stream. This prevents poison messages from blocking the pipeline.
6. **Eventual Consistency**: The chat service remains fully functional even if the ingestion worker crashes or PostgreSQL is temporarily unavailable. Telemetry accumulates in Redis Streams and is processed when the worker recovers.

### Provider Abstraction & LLM SDK
We built a custom `inferflow-llm-sdk` to normalize interactions with LLMs and keep the `chat-service` entirely agnostic of the underlying provider logic.

1. **Normalized Contracts**: The SDK defines abstract `StreamChunk` and `ChatCompletionResult` models. The `chat-service` only interacts with these normalized types.
2. **Provider Implementations**: 
   - **Gemini**: Implemented via `GeminiProvider` using the modern `google-genai` SDK.
   - **OpenAI**: Implemented via `OpenAIProvider` using the official `openai` async Python SDK.
3. **Dynamic Provider Resolution**: The frontend queries the `/api/v1/models` endpoint for a registry of supported models. When a user sends a message, they specify the model ID. The backend dynamically looks up the provider for that model, initializes it with the correct API key, and streams the response.
4. **Cancellation Lifecycle**: Streams can be cancelled dynamically via the `/api/v1/chat/cancel/{conversation_id}` endpoint. The `StreamManager` terminates the active `asyncio.Task`, which safely stops the generator and cleans up resources without raising uncaught exceptions. This prevents hanging TCP connections and wasted tokens.

### Frontend (`apps/frontend/`)
- React + Vite + TypeScript + Tailwind CSS
- Minimal chat UI with SSE-ready architecture
- Future: conversation management, model selection, real-time dashboard

### Chat Service (`apps/chat-service/`)
- FastAPI with async request handling
- SSE streaming endpoint for token-by-token responses
- Publishes inference events to Redis Streams (fire-and-forget)
- Router → Service → LLM SDK layered architecture

### Ingestion Worker (`apps/ingestion-worker/`)
- Standalone async Python process (not a web server)
- Redis Streams consumer group member
- Persists conversations, messages, and inference logs to PostgreSQL
- Graceful shutdown handling with signal trapping

### Monitoring Service (`apps/monitoring-service/`)
- FastAPI with WebSocket endpoints
- Consumes raw events from Redis Streams (independent consumer group)
- Real-time event fanout to connected dashboard clients
- Metrics aggregation (latency, throughput, error rates)

---

## Event Flow

```
User sends message
        │
        ▼
┌── Chat Service ──┐
│                  │
│  1. Load context │ (future: from PostgreSQL)
│  2. Call LLM     │ (via llm-sdk)
│  3. Stream SSE   │ ──────────► User sees tokens
│  4. XADD event   │ ──────────► Redis Streams (fire-and-forget)
│                  │
└──────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                                   ▼
┌── Ingestion ──┐                    ┌── Monitoring ──┐
│               │                    │                │
│  XREADGROUP   │                    │  XREADGROUP    │
│  Validate     │                    │  Aggregate     │
│  Persist      │                    │  Fanout via WS │
│  XACK         │                    │  XACK          │
│               │                    │                │
└───────────────┘                    └────────────────┘
```

### Key Design Decisions in the Event Flow

**Why fire-and-forget?**
The chat service publishes events to Redis Streams without waiting for acknowledgment from downstream consumers. This means inference latency is never blocked by database writes or monitoring processing. If the ingestion worker is temporarily down, events accumulate in the stream and are processed when the worker recovers.

**Why inference should not wait for persistence:**
- LLM inference is the bottleneck (100ms–10s). Adding DB write latency is unnecessary.
- Users care about response speed, not whether the message was persisted.
- Persistence can be retried; inference cannot be "un-shown" to the user.
- Decoupling allows independent scaling of inference and persistence.

**Why monitoring consumes raw events:**
The monitoring service has its own consumer group, reading the same stream independently. This avoids the ingestion worker becoming a bottleneck for real-time dashboards. Both consumers process events at their own pace without affecting each other.

---

## Schema Design

### conversations
```sql
CREATE TABLE conversations (
    id          UUID PRIMARY KEY,
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB DEFAULT '{}'
);
```

### messages
```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);
```

### inference_logs
```sql
CREATE TABLE inference_logs (
    id                UUID PRIMARY KEY,
    conversation_id   UUID NOT NULL REFERENCES conversations(id),
    message_id        UUID REFERENCES messages(id),
    model             TEXT NOT NULL,
    provider          TEXT,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    latency_ms        DOUBLE PRECISION,
    finish_reason     TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata          JSONB DEFAULT '{}'
);
```

### Schema Design Decisions

**Why are messages and inference_logs separated?**
- **Different access patterns**: Messages are read frequently (conversation history). Inference logs are queried for analytics and debugging.
- **Different retention policies**: You might archive old inference logs aggressively while keeping message history longer.
- **Cleaner data model**: Mixing operational telemetry (tokens, latency, model) into user-facing content bloats the messages table.
- **1:N potential**: A single message could involve multiple inference calls (retries, fallbacks).

**Why JSONB metadata?**
- Provider-specific response data varies wildly (OpenAI returns `logprobs`, Anthropic returns `stop_reason`).
- Avoids schema migrations for every new field from every provider.
- Useful for A/B testing metadata, feature flags, and request tracing.
- Queryable in PostgreSQL (`metadata->>'key'`) without sacrificing relational integrity.

**Why normalized inference events?**
- Enables aggregate analytics: average latency by model, cost by provider, error rates over time.
- Supports operational dashboards without scanning message content.
- Foundation for future cost tracking and usage billing.

---

## Tradeoffs & Engineering Decisions

### Why Redis Streams instead of Kafka?
- **Operational simplicity**: Redis is already needed for caching. No additional infrastructure.
- **Good enough**: At our scale (thousands of events/sec), Redis Streams provides ordered, persistent, consumer-group-based messaging.
- **Low latency**: Redis is in-memory. Event publishing adds <1ms overhead.
- **Migration path**: The consumer group API is conceptually similar to Kafka consumer groups. Migration to Kafka is straightforward when needed.

### Why PostgreSQL instead of MongoDB?
- **Relational integrity**: Conversations → Messages → Inference Logs have clear relational structure.
- **JSONB for flexibility**: PostgreSQL's JSONB gives MongoDB-like flexibility for metadata without sacrificing ACID guarantees.
- **Query power**: Complex analytics queries (join inference logs with messages, aggregate by model) are natural in SQL.
- **Ecosystem**: Better tooling for migrations (Alembic), ORMs (SQLAlchemy), and monitoring.

### Why FastAPI?
- **Async-native**: Built on Starlette with native `async/await` support. No thread pool hacks.
- **Type-safe**: Pydantic models for request/response validation. Self-documenting OpenAPI spec.
- **SSE support**: `sse-starlette` integrates cleanly for streaming responses.
- **Performance**: One of the fastest Python web frameworks.

### Why async-first?
- LLM API calls are I/O-bound (network requests to external providers). Async enables high concurrency without threads.
- Redis and PostgreSQL both have async client libraries.
- A single process can handle thousands of concurrent connections.

### Why SSE for chat streaming?
- **Unidirectional**: Chat responses flow server→client. No need for bidirectional communication.
- **HTTP-native**: Works through proxies, load balancers, and CDNs without special configuration.
- **Auto-reconnect**: The `EventSource` API handles reconnection automatically.
- **Simpler than WebSocket**: No connection upgrade, no frame parsing, no heartbeat management.

### Why WebSocket for monitoring?
- **Bidirectional**: Dashboard clients need to send subscription filters and receive event updates.
- **Low overhead**: Persistent connection avoids HTTP overhead for high-frequency metric updates.
- **Real-time**: Sub-millisecond delivery for live dashboards.

### Why not overengineer initially?
- **Scaffold first**: Establish clean service boundaries and communication patterns.
- **Implement incrementally**: Each service can be developed independently.
- **Avoid premature optimization**: Redis Streams is sufficient until proven otherwise.
- **Keep it boring**: Use well-understood tools (PostgreSQL, Redis, FastAPI) that the team already knows.

---

## Scalability Strategy

### Current Architecture (Single Instance)
Each service runs as a single process. Redis and PostgreSQL are single instances. This is sufficient for development and initial production deployment.

### Near-Term Scaling

**Redis Consumer Groups**
- Multiple ingestion workers share the load via consumer groups
- Each message is delivered to exactly one worker in the group
- Workers can be added/removed without downtime

**Horizontal Worker Scaling**
```
                    ┌── Worker 1 ──► PostgreSQL
Redis Streams ──────┼── Worker 2 ──► PostgreSQL
                    └── Worker 3 ──► PostgreSQL
```

**Replayability**
- Redis Streams retain messages until explicitly trimmed
- New consumer groups can replay the entire stream from the beginning
- Useful for backfilling new analytics tables or reprocessing after bug fixes

### Medium-Term Scaling

**Dead-Letter Queues**
- Failed events are moved to a separate stream after N retries
- Prevents poison messages from blocking the pipeline
- Enables manual inspection and reprocessing

**Connection Pooling**
- PostgreSQL connection pools (via asyncpg) for efficient DB access
- Redis connection pools for multiplexed stream operations

### Long-Term Scaling

**Kafka Migration**
- When Redis Streams' single-node throughput becomes a bottleneck
- Kafka provides partitioned topics, multi-broker replication, and higher throughput
- Consumer group semantics translate directly

**Kubernetes Deployment**
- Each service becomes a Deployment with HPA (Horizontal Pod Autoscaler)
- Redis and PostgreSQL move to managed services (ElastiCache, RDS)
- Ingestion workers scale based on stream lag metrics

---

## Future Improvements

- [ ] **Authentication & Authorization** — JWT-based auth, session management
- [ ] **RBAC** — Role-based access control for multi-user environments
- [ ] **OpenTelemetry** — Distributed tracing across all services
- [ ] **Prometheus/Grafana** — Metrics collection and dashboarding
- [ ] **Multi-Model Routing** — Route requests to different LLM providers based on task type
- [ ] **Rate Limiting** — Per-user and per-API-key rate limiting
- [ ] **Analytics Pipeline** — Aggregate inference data for cost analysis and usage patterns
- [ ] **Conversation Search** — Full-text search across message history
- [ ] **File Attachments** — Support for image and document uploads
- [ ] **Prompt Templates** — System prompt management and versioning

---

## Project Structure

```
inferflow/
├── apps/
│   ├── frontend/              # React + Vite + TypeScript + Tailwind
│   │   ├── src/
│   │   │   ├── components/    # UI components
│   │   │   ├── App.tsx        # Root component
│   │   │   └── main.tsx       # Entry point
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── chat-service/          # FastAPI — inference + streaming
│   │   ├── app/
│   │   │   ├── routers/       # API route handlers
│   │   │   ├── services/      # Business logic
│   │   │   ├── schemas.py     # Pydantic models
│   │   │   ├── config.py      # Service configuration
│   │   │   └── main.py        # FastAPI app
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── ingestion-worker/      # Async Redis Streams consumer
│   │   ├── worker/
│   │   │   ├── consumer.py    # Stream consumer loop
│   │   │   ├── processor.py   # Event processing logic
│   │   │   ├── config.py      # Worker configuration
│   │   │   └── main.py        # Entry point
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── monitoring-service/    # FastAPI — WebSocket + metrics
│       ├── app/
│       │   ├── routers/       # Health + WebSocket endpoints
│       │   ├── services/      # Connection manager + metrics
│       │   ├── config.py      # Service configuration
│       │   └── main.py        # FastAPI app
│       ├── Dockerfile
│       └── pyproject.toml
│
├── packages/
│   ├── shared/                # Shared config + logging utilities
│   │   └── inferflow_shared/
│   └── llm-sdk/               # LLM provider abstraction (planned)
│       └── inferflow_llm/
│
├── infrastructure/
│   └── init-db/               # PostgreSQL initialization scripts
│
├── docker-compose.yml         # Full-stack local orchestration
├── Makefile                   # Developer commands
├── .env.example               # Environment variable template
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & Docker Compose

### Local Development

The fastest and most reliable way to run the entire InferFlow platform locally is using Docker Compose. The setup is configured for **local developer ergonomics**, meaning:
- All source code is mounted as volumes, enabling hot-reloading for both the frontend (Vite) and backend (FastAPI/uvicorn).
- Dependencies and startup order are handled automatically. You don't need to manually orchestrate the services.
- Data for PostgreSQL and Redis are persisted in Docker volumes.

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Add your LLM API keys to .env
# GEMINI_API_KEY="..."

# 3. Start the entire platform (Frontend, APIs, Workers, Redis, DB)
make docker-up --build

# 4. View logs
make docker-logs
```

Once running, access the platform at:
- Frontend & Dashboard: http://localhost:5173
- Chat Service API: http://localhost:8000
- Monitoring API: http://localhost:8001

To stop the platform and wipe the database/volumes:
```bash
make docker-down
```

### Manual Run (Without Docker)

If you prefer to run services manually outside of Docker (e.g., for debugging):

```bash
# Start infrastructure
docker compose up redis postgres -d

# Install dependencies
make install

# Run services (in separate terminals)
make run-chat        # Chat service
make run-monitoring  # Monitoring service
make run-frontend    # Frontend
make run-ingestion   # Ingestion worker
```

### Available Commands

```bash
make help            # Show all commands
make install         # Install all dependencies
make run             # Show service run instructions
make lint            # Lint all Python services
make format          # Format all Python services
make build           # Build all Docker images
make docker-up       # Start all services
make docker-down     # Stop all services
make clean           # Remove build artifacts
```

---

## License

MIT
