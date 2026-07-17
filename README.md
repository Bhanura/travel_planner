# Booking Agents Backend

A FastAPI-based booking system with hotel and flight agents powered by LangChain.


## Setup

### 1. Create Virtual Environment
```bash
python -m venv env
```

Activate the virtual environment:
- **Windows (CMD)**:
  ```bash
  env\Scripts\activate
  ```
- **Windows (PowerShell)**:
  ```bash
  env\Scripts\Activate.ps1
  ```
- **macOS/Linux**:
  ```bash
  source env/bin/activate
  ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

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
- `HOTEL_PROVIDER_BASE_URL`: Hotel provider base URL used by the hotel MCP server.
- `FLIGHT_PROVIDER_BASE_URL`: Flight provider base URL used by the flight MCP server.
- `TRAVEL_PLANNER_API_URL`: Backend URL used by the Gradio frontend.
- `ALLOWED_ORIGINS`: Comma-separated frontend origins allowed by FastAPI CORS.

### 4. Run the Backend
```bash
python main.py
```

### 5. Run the Frontend
In a new terminal (with the virtual environment activated):
```bash
python frontend.py
```

## API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/hotels` | GET | Get all hotels | `curl http://localhost:8000/hotels` |
| `/flights` | GET | Get all flights | `curl http://localhost:8000/flights` |
| `/chat` | POST | Chat with agent | See below |

### Chat Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "find me a hotel in NYC"}'
```

**Other queries to try:**
- "show me all hotels"
- "book a hotel in Miami"
- "find flights from New York to London"
- "show all flights"

## Gradio Chat UI

A Gradio chat interface is available in `frontend.py`.

Run the FastAPI backend first:

```bash
python main.py
```

Then start the Gradio UI:

```bash
python frontend.py
```

Open the local Gradio URL shown in the terminal and ask for flights or hotels.

## Tech Stack

- **FastAPI** - Web framework
- **LangChain** - Agent framework
- **OpenAI** - LLM (GPT-4o-mini)
- **python-dotenv** - Environment config
