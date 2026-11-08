# Text2SQL with an MCP Agent

Text2SQL lets users ask questions about a SQLite database in natural language. A
LangChain agent uses a Groq chat model to understand the request, inspect the
database schema, create and check SQL, and return an answer. The agent's
database tools are exposed through a separate MCP server. Redis stores
LangGraph checkpoints so a conversation can continue across requests.

## Highlights

- **Natural language to SQL:** Ask questions in plain language; the agent
  chooses relevant tables and columns, checks its SQL, and uses the query
  results to answer.
- **MCP tools and resources:** The MCP server provides tools to list tables,
  inspect table schemas and sample rows, check a query, and execute it. It also
  exposes the database schema as an MCP resource.
- **Conversation memory:** Each conversation ID is used as the LangGraph
  checkpoint thread ID. Redis stores conversation state between requests.
- **Streaming API:** The chat endpoint uses Server-Sent Events (SSE) to stream
  response tokens and tool-call information.
- **Containerized services:** Docker Compose starts the API and Redis, persists
  Redis data in a named volume, and mounts the SQLite database read-only into
  the API container.

## How it fits together

```text
Client
  │ POST /api/chat (SSE)
  ▼
FastAPI ── ChatService ── LangChain/LangGraph agent ── Groq chat model
                                  │
                                  ├── MCP over stdio ── SQLite tools/resource
                                  └── Redis checkpointer
```

At API startup, `AgentFactory` creates the async Redis checkpointer, connects to
the MCP server over standard input/output, loads its tools, and constructs the
agent. The API keeps these resources open for the application lifespan.

For each chat request, the conversation service uses the supplied
`conversation_id`, or creates one if it is missing. That ID is returned in a
`conversation` SSE event; send it with later requests to continue the same
conversation. Redis stores the checkpoint data, not the SQLite database.

## Requirements

- Python 3.13 or later and [uv](https://docs.astral.sh/uv/) for local
  development.
- Docker Desktop or Docker Engine with the Compose plugin for container use.
- A Groq API key and a chat model supported by the configured LLM provider.
- A SQLite database. The repository includes `data/Chinook.db` as an example.

## Run with Docker Compose

1. Copy the example environment file and edit it:

   ```powershell
   Copy-Item .env.example .env
   ```

   Set `GROQ_API_KEY` and `CHAT_MODEL_NAME` to your credentials and a model
   supported by your provider. Keep secrets in `.env`; do not commit it.

2. Start the API and Redis:

   ```powershell
   docker compose up --build
   ```

3. Open the API documentation at <http://localhost:8000/docs>. The health
   endpoint is <http://localhost:8000/api/health>.

Compose connects the app to Redis using the internal Docker hostname
`redis:6379`, overrides `DB_PATH` to `/app/data/Chinook.db`, and mounts the
repository's `data` directory read-only. Set `API_PORT` in `.env` to change the
host port (the container continues to listen on port 8000).

Stop the services with:

```powershell
docker compose down
```

This leaves the `redis_data` volume intact. To also remove saved Redis
checkpoints, run `docker compose down --volumes`; this permanently deletes that
volume's data.

## Run locally

1. Create and configure `.env` as described above. For a local run, set:

   ```dotenv
   DB_PATH=data/Chinook.db
   REDIS_URL=redis://localhost:6379/0
   ```

2. Install project dependencies and start Redis:

   ```powershell
   uv sync --frozen
   docker compose up -d redis
   ```

3. Start the API:

   ```powershell
   uv run uvicorn src.api.main:app --reload
   ```

The API is available at <http://localhost:8000>; interactive documentation is
at <http://localhost:8000/docs>.

## API

### `GET /api/health`

Returns a simple health response:

```json
{"status":"ok"}
```

### `POST /api/chat`

Request body:

```json
{
  "message": "Which music genre has the most tracks?",
  "conversation_id": "optional-existing-conversation-id"
}
```

`message` is required and cannot be empty. `conversation_id` is optional. If
omitted, the server creates an ID; capture it from the first SSE event and send
it in subsequent requests to retain conversation context.

Example request:

```bash
curl -N http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Which music genre has the most tracks?"}'
```

The response is `text/event-stream`. Events are:

| Event | Data |
|---|---|
| `conversation` | The conversation ID for this request. |
| `token` | A streamed answer token and the conversation ID. |
| `tool_call` | Tool-call information and the conversation ID. |
| `done` | Indicates that the response completed. |
| `error` | Indicates that the assistant could not complete the request. |

Example event:

```text
event: conversation
data: {"conversation_id":"..."}
```

## Configuration

| Variable | Purpose |
|---|---|
| `CHAT_MODEL_NAME` | Model name passed to the configured chat provider. |
| `GROQ_API_KEY` | API key for Groq. |
| `llm_type` | LLM provider selection; currently the factory supports `groq`. |
| `temperature` | Model sampling temperature. |
| `max_retries` | Provider retry limit. |
| `DB_PATH` | SQLite database path. Compose sets this to the mounted example database path. |
| `REDIS_URL` | Redis connection URL. Compose sets this to `redis://redis:6379/0` for the API container. |
| `API_PORT` | Host port published by Docker Compose; defaults to `8000`. |

See [.env.example](./.env.example) for a template.

## Project layout

```text
config/                 Application settings
mcp_server/              MCP server, database tools, and schema resource
src/api/                 FastAPI app and HTTP routes
src/services/            Chat streaming and conversation ID handling
src/text2sql/            Agent, LLM factory, prompts, and SQL tools
data/Chinook.db          Example SQLite database
Dockerfile               API container image
docker-compose.yml       API and Redis services
```

## Important notes

- The agent prompt instructs the model not to make data-changing SQL statements.
  Treat this as model guidance, not a complete security boundary. Review and
  constrain database access and SQL execution before exposing the service to
  untrusted users or production data.
- The API currently has no authentication or per-user authorization. Anyone
  who can reach it can submit chat requests and supply a conversation ID.
- Keep `.env` and API keys out of source control. Use an appropriate secrets
  manager for deployed environments.
- Redis stores conversation checkpoints. Protect Redis and its volume as
  application data; do not expose the Redis port publicly.