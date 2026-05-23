# InferFlow Architecture Design

This document details the deeper architectural decisions, data flows, and scaling considerations for the InferFlow platform. For setup instructions and a high-level overview, please refer to the main [README.md](./README.md).

```text
┌─────────────┐     SSE Stream      ┌──────────────────┐
│             │ ◄────────────────── │                  │
│   Frontend  │                     │   Chat Service   │──── LLM Provider
│   (React)   │ ────────────────►   │   (FastAPI)      │     (OpenAI, etc.)
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
                 │ (Async Consumer) │                   │ (FastAPI + SSE)  │
                 │                  │                   │                  │
                 └────────┬─────────┘                   └──────────────────┘
                          │                                      │
                          │ INSERT                               │ SSE
                          ▼                                      ▼
                 ┌──────────────────┐                   ┌──────────────────┐
                 │                  │                   │                  │
                 │   PostgreSQL     │                   │   Dashboard      │
                 │   (Data Store)   │                   │   (React)        │
                 │                  │                   │                  │
                 └──────────────────┘                   └──────────────────┘
```

---

## 1. Ingestion & Event Flow

The ingestion pipeline is designed as an asynchronous, fire-and-forget process to ensure that the core chat experience remains fast and unimpeded by database write latency.

```text
User sends message
        │
        ▼
┌── Chat Service ──┐
│                  │
│  1. Load context │ (from PostgreSQL via API)
│  2. Call LLM     │ (via inferflow-llm-sdk)
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
│  Persist      │                    │  Fanout via SSE│
│  XACK         │                    │                │
│               │                    │                │
└───────────────┘                    └────────────────┘
```

- **Event Publishing**: When a user sends a message and the LLM responds, the Chat Service streams the response back via Server-Sent Events (SSE). Concurrently, it wraps the generation process in a `TelemetryWrapper` which publishes raw inference events (e.g., `InferenceStartedEvent`, `InferenceCompletedEvent`) to a Redis Stream (`llm.inference.events`) asynchronously. 
- **Consumer Group Processing**: A standalone Ingestion Worker joins the `ingestion-group` Redis consumer group using `XREADGROUP`. This ensures that each inference event is read exactly once by the worker pool.
- **Pipeline Stages**: The worker consumes an event, validates its schema, redacts any sensitive PII (like emails or credit cards from error messages), and durably persists the telemetry to PostgreSQL. (Note: The actual chat messages and conversations are persisted to PostgreSQL directly by the Chat Service API. The ingestion worker only handles the operational telemetry).
- **Idempotency & Acknowledgement**: Events are only acknowledged (`XACK`) after a successful PostgreSQL write. The database enforces uniqueness via a `request_id` constraint (`ON CONFLICT DO NOTHING`), making the ingestion pipeline completely safe against duplicate deliveries or worker restarts.
- **Dead-Letter Routing**: Unprocessable or malformed events are routed to a dead-letter stream (`llm.inference.invalid`) rather than blocking the main pipeline.

## 2. Logging Strategy & Telemetry

Observability is decoupled from the LLM generation logic. 

- **TelemetryWrapper**: The Gemini and OpenAI SDKs focus purely on streaming tokens. The custom wrapper intercepts the stream to calculate `ttft_ms` (Time To First Token), generate `request_id`s, track token usage, and record total latency.
- **Normalized Event Contracts**: The system uses a shared package (`inferflow_shared`) to define standard event shapes. Whether the model is from OpenAI or Google Gemini, the telemetry emitted to the ingestion pipeline remains uniformly structured.
- **Zero-Block Observability**: The producer uses a robust `try-except` mechanism to publish events. If Redis is temporarily unreachable, the telemetry event is dropped, but the user's inference stream continues uninterrupted.

## 3. Scaling Considerations

The platform is designed to scale horizontally across all tiers:

- **Frontend & Chat Service**: Both are stateless applications. The Chat Service uses FastAPI's native `async/await` to handle thousands of concurrent SSE connections per process. They can be scaled out infinitely behind a load balancer.
- **Ingestion Workers**: Redis Streams allow multiple ingestion workers to share the load. Adding more workers linearly increases the ingestion throughput without duplicating event processing.

```text
                    ┌── Worker 1 ──► PostgreSQL
Redis Streams ──────┼── Worker 2 ──► PostgreSQL
                    └── Worker 3 ──► PostgreSQL
```

- **Monitoring Fanout**: The Monitoring Service reads from the same Redis Stream using a different consumer group. This avoids the ingestion worker becoming a bottleneck for real-time dashboards. Both consumers process events at their own pace.
- **Database Layer**: PostgreSQL connection pools (via `asyncpg`) provide efficient database access. For long-term scaling, the Redis Streams could be transparently replaced by Apache Kafka to support multi-broker replication and higher throughput partition semantics.

## 4. Failure Handling Assumptions

InferFlow embraces the philosophy of "Eventual Consistency" to maximize availability:

- **Redis Unavailability**: If Redis goes down, telemetry events cannot be published. The system will drop these logging events, but the core conversational experience (Chat Service to LLM Provider to User) will continue unaffected.
- **PostgreSQL Unavailability**: If the primary database goes down, the Chat Service remains fully functional for active interactions. The Ingestion Worker will fail to persist events, leaving them unacknowledged in the Redis Stream. Once PostgreSQL recovers, the workers will naturally resume processing the backlog.
- **LLM Provider Outages**: The Chat Service dynamically resolves providers. If one provider times out or fails, the resulting error is gracefully streamed to the user and published to the telemetry pipeline for dashboard visibility. The user can simply switch to an alternative model and resume the conversation.
- **Worker Crashes**: Ingestion Workers trap termination signals to execute graceful shutdowns. If a worker crashes mid-processing, the unacknowledged messages are automatically redelivered to other healthy workers in the consumer group.
