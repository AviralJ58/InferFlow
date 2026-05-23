# InferFlow

**Intelligent conversation platform with streaming LLM responses, event-driven ingestion, and real-time monitoring.**

InferFlow is an async-first, event-driven platform for building production-grade conversational AI experiences. It separates inference, persistence, and monitoring into independent services connected via Redis Streams — enabling each component to scale, fail, and evolve independently.

## Key Features

- **Multi-provider Support**: Provider-agnostic LLM SDK with dynamic routing between OpenAI and Google Gemini.
- **Streaming Responses**: Server-Sent Events (SSE) for real-time token-by-token LLM responses.
- **Latency + Throughput + Errors Dashboards**: Real-time metrics visualization via SSE fanout.
- **Docker Compose One-Command Setup**: Entire platform orchestrates seamlessly for local development.
- **Event-Based Architecture**: Fire-and-forget event publishing; inference never waits for persistence.
- **PII Redaction**: Automatic redaction of sensitive information (emails, credit cards) before database persistence.
- **Rich Frontend UI**: The React interface supports canceling a running generation stream, listing historical conversations, and resuming existing conversations.

---

## Quick Start

The fastest and most reliable way to run the entire InferFlow platform locally is using our **Docker Compose one-command setup**.

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ and Python 3.11+ (for local un-containerized debugging)

### Running Locally

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Add your LLM API keys to .env (e.g. GEMINI_API_KEY="..." or OPENAI_API_KEY="...")

# 3. Start the entire platform (Frontend, APIs, Workers, Redis, DB)
make docker-up --build

# 4. View logs
make docker-logs
```

Access the platform at:
- **Frontend & Chat**: http://localhost:5173
- **Monitoring Dashboard**: http://localhost:5173/dashboard
- **Chat API**: http://localhost:8000

---

## Brief Architecture Overview

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

InferFlow embraces separation of concerns. The hot path (user chatting) is decoupled from the cold path (saving data and analyzing metrics).

1. **Frontend (React)**: Communicates with the Chat Service to stream LLM tokens and manage the conversation UI.
2. **Chat Service (FastAPI)**: Manages provider routing and SSE streaming. It directly persists conversations and user messages to PostgreSQL. Concurrently, it publishes operational inference telemetry events asynchronously to a Redis Stream without waiting for downstream services.
3. **Redis Streams**: Acts as the central event bus for the system.
4. **Ingestion Worker (Python Async)**: Consumes from Redis, redacts PII, and persists the operational inference telemetry logs to PostgreSQL.
5. **Monitoring Service (FastAPI)**: Independently consumes the same Redis stream and calculates real-time metrics, serving them to the dashboard via SSE (Server-Sent Events).

> **Deep Dive**: For a detailed breakdown of the ingestion flow, logging strategy, scaling considerations, and failure handling assumptions, please read the [Architecture Design Document](./architecture.md).

---

## Schema Design Decisions

We maintain a strict separation between user content and operational telemetry:

- **`conversations` & `messages`**: Stores user-facing chat histories.
- **`inference_logs`**: Stores operational data (prompt tokens, completion tokens, latency_ms, finish_reason).
- **Why Separate?**: Mixing telemetry into the messages table bloats the core chat data model. Separation allows for different retention policies (e.g., archiving logs while keeping chat histories).
- **JSONB Metadata**: Both messages and inference logs utilize a `JSONB` metadata column. Provider-specific response data varies wildly (e.g., OpenAI returns `logprobs`, Anthropic returns `stop_reason`). JSONB provides MongoDB-like flexibility for provider specifics without sacrificing PostgreSQL's relational integrity.

---

## Tradeoffs Made

- **SSE vs WebSockets (for Chat)**: We chose Server-Sent Events (SSE) for the chat interface because chat generation is strictly unidirectional (Server → Client). SSE is HTTP-native, easier to load-balance, and auto-reconnects, making it significantly simpler than managing bidirectional WebSocket frames.
- **SQL (PostgreSQL) vs NoSQL**: We opted for PostgreSQL. Conversations, messages, and logs have clear relational structures. PostgreSQL's `JSONB` gives us the flexibility of NoSQL for unstructured metadata, while preserving ACID guarantees and powerful aggregate query capabilities for future analytics.
- **Consistency vs Availability (Eventual Persistence vs Latency)**: We prioritize **availability and low latency** over immediate consistency. LLM inference is the bottleneck. The Chat Service utilizes a "fire-and-forget" pattern, publishing telemetry to Redis without waiting for the Ingestion Worker to save it to PostgreSQL. If the database goes down, users can still chat seamlessly; data accumulates in Redis and is persisted eventually.

---

## Future Improvements (With More Time)

If given more time, the following improvements would be prioritized:

1. **Improve caching for faster TTFT**: Implement Redis-backed caching for conversation history and provider responses to reduce the time to first token (TTFT).
2. **Implement comprehensive Rate Limiting**: Implement Redis-backed token bucket rate limiting on the Chat Service API to protect against abuse per user or IP.
3. **Deploy on self-hosted Kubernetes**: Containerize the workloads into Helm charts and deploy to a self-hosted K8s cluster, utilizing Horizontal Pod Autoscalers (HPA) for the Ingestion Worker based on Redis stream lag.
4. **Prometheus / Grafana**: Replace the custom monitoring service with industry-standard Prometheus metrics scraping and Grafana dashboards for deeper operational visibility.
5. **Improve Analytics**: Build aggregate materialized views or periodic cron jobs to summarize inference data for long-term cost analysis, latency tracking by provider, and identifying user usage patterns.
