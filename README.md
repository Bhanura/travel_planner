# TripWeaver - MCP Based Multi-Agent Travel Planner

TripWeaver is a travel planning assistant that helps users search hotels, search flights, and book hotel rooms through a multi-agent workflow.

The project uses a FastAPI backend, LangGraph agent routing, LangChain tools, MCP servers for provider access, and a Gradio frontend with streaming agent progress.

## Features

- Search hotels by city.
- Search flights by route.
- Ask follow-up questions when required details are missing.
- Route requests to hotel, flight, or general travel agents.
- Access hotel and flight providers through MCP servers.
- Stream agent activity through `/chat/stream`.
- Show agent progress in the frontend.
- Display hotel and flight results in an expandable results panel.
- Support session-based hotel booking with user confirmation.
- Handle external service failures with friendly messages.

## Architecture

TripWeaver is organized into five main layers:

1. **Gradio Frontend**
   - Runs from the `frontend/` package.
   - Sends user messages to the FastAPI backend.
   - Consumes `/chat/stream` NDJSON events.
   - Shows chat messages, agent progress, quick prompts, and expandable travel results.

2. **FastAPI Backend**
   - Runs from `main.py`.
   - Exposes `/chat` and `/chat/stream`.
   - Builds the initial graph state.
   - Maintains lightweight in-memory session state with `session_id`.

3. **LangGraph Agent Workflow**
   - Defined in `agents/graph.py`.
   - Routes requests through `router`.
   - Sends hotel requests to `hotel_node`.
   - Sends flight requests to `flight_node`.
   - Sends general requests to `unknown_node`.
   - Uses `generate_response` to create final assistant text.

4. **LangChain Tool Layer**
   - Defined in `agents/tools.py`.
   - Keeps stable tool names such as `search_hotel`, `search_flights`, `book_hotel`, and `book_flight`.
   - Calls the MCP client instead of directly calling external provider APIs.

5. **MCP Provider Layer**
   - Hotel MCP server: `mcp_servers/hotel_server.py`
   - Flight MCP server: `mcp_servers/flight_server.py`
   - Handles provider-specific HTTP requests.
   - Keeps external service logic separated from the agent workflow.

## Project Structure

```text
.
|-- agents/
|   |-- entity.py        # LangGraph state schema
|   |-- graph.py         # LangGraph workflow definition
|   |-- llm.py           # LLM configuration
|   |-- mcp_client.py    # MCP client adapter
|   |-- nodes.py         # Router, hotel, flight, unknown, and response nodes
|   |-- prompts.py       # LLM extraction and fallback prompts
|   `-- tools.py         # LangChain tools that call MCP
|-- mcp_servers/
|   |-- flight_server.py # Flight MCP tools
|   |-- hotel_server.py  # Hotel MCP tools
|   `-- provider_utils.py
|-- entity.py            # FastAPI request/response models
|-- frontend/            # Modular Gradio frontend package
|-- main.py              # FastAPI backend
|-- requirements.txt
`-- .env.example
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv env
```

Activate the virtual environment:

Windows CMD:

```bash
env\Scripts\activate
```

Windows PowerShell:

```powershell
env\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source env/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependency Management

TripWeaver uses two runtime dependency files:

- `requirements.in` contains the direct dependencies intentionally used by the application.
- `requirements.txt` is generated from `requirements.in` and pins all direct and transitive dependency versions for reproducible CI and deployment.

Install the tested runtime environment with:

```bash
pip install -r requirements.txt
```

Do not edit generated dependency versions directly in `requirements.txt`. To update dependencies, edit `requirements.in`, install the tested compiler version, and regenerate the lock:

```bash
python -m pip install pip-tools==7.5.3
python -m piptools compile requirements.in --output-file requirements.txt --resolver=backtracking --strip-extras
```

The lock was generated with Python 3.11. Windows-only MCP support is protected by a platform marker, so `pywin32` is skipped on Linux deployment hosts. A clean Linux installation will also be verified by CI.

### 3. Configure Environment Variables

Copy `.env.example` to `.env` in the project root, then update the values for your local setup.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Environment variables:

- `OPENAI_API_KEY`: API key used by the LLM.
- `OPENAI_MODEL`: OpenAI chat model name.
- `LOG_LEVEL`: Application logging verbosity. Use `INFO` in production and `DEBUG` temporarily during development or diagnosis.
- `HOTEL_PROVIDER_BASE_URL`: Hotel provider base URL used by the hotel MCP server.
- `FLIGHT_PROVIDER_BASE_URL`: Flight provider base URL used by the flight MCP server.
- `TRAVEL_PLANNER_API_URL`: Backend URL used by the Gradio frontend.
- `ALLOWED_ORIGINS`: Required comma-separated explicit frontend origins allowed by FastAPI CORS. Wildcard `*` is rejected.

The real `.env` file is ignored by Git. Do not commit API keys.

## Running The App

### Run The Backend

```bash
python main.py
```

The backend runs at:

```text
http://127.0.0.1:8000
```

### Run The Frontend

Open a second terminal with the virtual environment activated:

```bash
python -m frontend
```

The Gradio frontend usually runs at:

```text
http://127.0.0.1:7860
```

## MCP Server Notes

The app starts MCP servers through the MCP client adapter when LangChain tools are called.

The MCP server modules can also be started directly for development checks:

```bash
python -m mcp_servers.hotel_server
python -m mcp_servers.flight_server
```

Manual MCP server startup waits for stdio MCP input. Pressing `Ctrl+C` during a manual run may show an async cancellation traceback, which is expected during local testing.

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Identifies the TripWeaver API and links to health and API documentation. |
| `/health` | GET | Reports backend liveness and safe configuration readiness without calling external services. |
| `/hotels` | GET | Development/debug endpoint that lists hotels through the hotel tool. |
| `/flights` | GET | Development/debug endpoint that lists flights through the flight tool. |
| `/chat` | POST | Normal JSON chat endpoint. |
| `/chat/stream` | POST | NDJSON streaming chat endpoint used by the frontend. |

### GET `/health`

The health endpoint returns HTTP 200 while the FastAPI application is running. It reports whether required LLM, hotel-provider, and flight-provider configuration is present without exposing API keys, provider URLs, or other secret values.

The endpoint does not call MCP servers or external providers. A missing dependency is reported as `degraded` so one unavailable travel service does not make unrelated agents unusable.

Example:

```json
{
  "status": "healthy",
  "service": "tripweaver-backend",
  "dependencies": {
    "llm_configured": true,
    "hotel_provider_configured": true,
    "flight_provider_configured": true
  }
}
```

### POST `/chat`

Request:

```json
{
  "message": "find hotels in Bangkok",
  "session_id": "demo-session-1"
}
```

Response:

```json
{
  "response": "I found 7 hotel options: ...",
  "hotels": [],
  "flights": null
}
```

PowerShell example:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"find hotels in Bangkok","session_id":"demo-session-1"}'
```

### POST `/chat/stream`

`/chat/stream` returns `application/x-ndjson`.

Each line is a JSON event.

Example stream:

```json
{"type":"activity","stage":"routing","message":"Understanding your request..."}
{"type":"activity","stage":"routing","message":"Choosing the right travel agent..."}
{"type":"activity","stage":"searching","message":"Found hotel options."}
{"type":"message","content":"I found 7 hotel options: ...","hotels":[...],"flights":null}
{"type":"done"}
```

PowerShell example:

```powershell
$response = Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "http://127.0.0.1:8000/chat/stream" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"find flights from BOM to DEL","session_id":"demo-session-1"}'

[System.Text.Encoding]::UTF8.GetString($response.Content)
```

## NDJSON Stream Event Format

| Event Type | Purpose |
| --- | --- |
| `activity` | Shows progress such as routing, searching, clarifying, or booking. |
| `message` | Contains the final assistant response and optional `hotels` or `flights` arrays. |
| `error` | Contains a safe user-facing error if streaming fails unexpectedly. |
| `done` | Marks the end of the stream. |

Activity event:

```json
{
  "type": "activity",
  "stage": "searching",
  "message": "Found hotel options."
}
```

Message event:

```json
{
  "type": "message",
  "content": "I found 7 hotel options: ...",
  "hotels": [],
  "flights": null
}
```

Error event:

```json
{
  "type": "error",
  "message": "Something went wrong while streaming your trip plan. Please try again in a moment."
}
```

Done event:

```json
{
  "type": "done"
}
```

## Example Prompts

Try these in the Gradio UI:

- `hotels in Bangkok`
- `hotels in Mumbai`
- `find flights from BOM to DEL`
- `find flights from Tokyo to Seoul`
- `I need to book a hotel`
- `book Shangri-La BKK 1`
- `Bhanu, bhanu@example.com, 2026-09-05 to 2026-09-06, single`
- `yes`

## Booking Flow

Hotel booking uses session memory and user confirmation:

1. User searches for hotels.
2. Backend stores the latest hotel results in the session.
3. User selects a hotel by name.
4. Backend maps the hotel name to the provider hotel ID.
5. Assistant asks for missing guest/date/room details.
6. Assistant shows a confirmation summary.
7. User confirms.
8. Backend calls the hotel booking MCP tool.
9. Assistant returns booking reference and total price.

## Error Handling

TripWeaver uses layered error handling:

- Agent nodes catch hotel/flight MCP failures and return service-specific friendly messages.
- The API layer catches unexpected graph failures around `graph.invoke(...)`.
- The streaming endpoint returns safe `error` events instead of raw stack traces.

Technical errors are kept in backend logs for debugging. User responses stay safe and readable.

## Deployment Notes

For deployment:

1. Deploy the FastAPI backend to a Python-compatible host.
2. Add production environment variables on the backend host.
3. Ensure the backend can launch MCP server modules.
4. Set `ALLOWED_ORIGINS` to the deployed frontend URL.
5. Deploy the Gradio frontend.
6. Set `TRAVEL_PLANNER_API_URL` in the frontend environment to the deployed backend URL.
7. Test `/chat` and `/chat/stream` after deployment.

Recommended production checks:

- Use HTTPS URLs.
- Configure `ALLOWED_ORIGINS` with the exact deployed frontend origin. Wildcard origins are rejected.
- Keep `.env` and API keys out of Git.
- Replace debug `print(...)` calls with structured logging before production use.

## Current Limitations

- Session memory is in process memory and resets when the backend restarts.
- Hotel name matching is still fuzzy for similar hotel names.
- Flight booking does not yet have the same natural selection flow as hotel booking.
- The app is not yet deployed.

## Secret Scanning

TripWeaver uses Gitleaks to scan the repository and complete Git history for accidentally committed API keys, tokens, passwords, and other credentials.

Verify the installed scanner:

```bash
gitleaks version
```

Scan all Git refs and redact any detected values from terminal output:

```bash
gitleaks git --redact=100 --no-banner --verbose --log-opts="--all" .
```

A successful scan exits with code `0`. Possible findings exit with code `1` and must be reviewed. If a real credential is detected, revoke or rotate it before cleaning the repository history. Never treat deleting the latest file as sufficient, because the credential may remain recoverable from an earlier commit.

The local `.env` file is ignored and must never be committed. `.env.example` contains names and safe placeholder/configuration values only.

## Notes

Short explanation:

```text
TripWeaver uses FastAPI, LangGraph, LangChain tools, MCP servers, and a Gradio frontend.
The backend routes user intent to hotel, flight, or general agents.
External provider calls are isolated behind MCP servers.
The frontend consumes NDJSON streaming events so users can see agent progress.
Structured hotel and flight results are shown in a separate expandable panel.
For booking, the app uses session memory and human confirmation so users can naturally select a hotel from previous results without manually providing internal IDs.
```

Key points to explain:

- MCP decouples provider API logic from agent logic.
- LangGraph manages routing between specialized nodes.
- `GraphState` carries extracted fields, results, and response text.
- Missing input handling prevents the agent from guessing.
- NDJSON streaming makes agent progress visible.
- Session state stores exact hotel/flight result objects for follow-up turns.
- Human-in-the-loop confirmation prevents accidental bookings.

## Tech Stack

- **FastAPI** - Backend API framework
- **Gradio** - Frontend chat UI
- **LangGraph** - Agent workflow routing
- **LangChain** - Tool abstraction and LLM integration
- **MCP Python SDK** - MCP server/client integration
- **OpenAI** - LLM provider
- **python-dotenv** - Environment variable loading
- **httpx** - Provider HTTP requests inside MCP servers
