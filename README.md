# Multi-Agent Travel Planning System — LangGraph + MCP + Supervisor + Guardrails + Human-in-the-Loop

A real-world multi-agent travel planner built with **LangGraph**. A supervisor agent validates the
request, decides which specialist agents to run, and routes work through them. Live data comes from
three **MCP servers** (Tavily, AviationStack, OpenWeatherMap). The draft itinerary is paused for
**human approval** before the final plan is produced, and conversation state is checkpointed in
**PostgreSQL** so a thread can be resumed.

This is **Part 3** of the series — it adds the Supervisor Agent, input Guardrails, Human-in-the-Loop
approval, and Docker packaging on top of Parts 1 and 2.

| Part | Focus | Repo | Video |
|---|---|---|---|
| 1 | Multi-Agent + Memory + APIs | [AI-Travel-Planning-System-using-LangGraph](https://github.com/codewithaarohi/AI-Travel-Planning-System-using-LangGraph) | [youtu.be/ctHby5vhDqg](https://youtu.be/ctHby5vhDqg) |
| 2 | Multi-Agent + Memory + MCP | [AI-Travel-Planning-App-using-LangGraph-and-MCP](https://github.com/codewithaarohi/AI-Travel-Planning-App-using-LangGraph-and-MCP) | [youtu.be/DjMX7o2EeV0](https://youtu.be/DjMX7o2EeV0) |
| 3 | Supervisor + Guardrails + HITL | this repo | — |

---

## Architecture

```mermaid
flowchart TD
    START([START]) --> SUP[supervisor<br/>guardrail + agent selection]
    SUP --> FL[flight_agent]
    SUP --> HO[hotel_agent]
    SUP --> WE[weather_agent]
    SUP --> BU[budget_agent]
    FL --> HO
    HO --> WE
    WE --> BU
    BU --> IT[itinerary_agent]
    SUP --> IT
    IT --> HA[human_approval<br/>interrupt]
    HA --> FR[final_response]
    FR --> END([END])
```

The supervisor picks a subset of agents; routing then walks `AGENT_ORDER`
(`flight → hotel → weather → budget → itinerary`) and skips any agent that wasn't selected.
`itinerary_agent` always runs.

### Agents

| Agent | What it does | Data source |
|---|---|---|
| `supervisor_agent` | Runs the input guardrail, then returns `selected_agents` + `trip_constraints` as JSON | LLM |
| `flight_agent` | Airports, airlines, duration, fare range, booking advice | AviationStack MCP + LLM |
| `hotel_agent` | Hotels and neighborhoods to stay in | Tavily MCP |
| `weather_agent` | Current conditions + 5-entry forecast | Weather MCP (OpenWeatherMap) |
| `budget_agent` | Cost categories, risks, savings, feasibility | LLM over prior agent output |
| `itinerary_agent` | Draft day-by-day plan for review | LLM over all prior output |
| `human_approval_agent` | `interrupt()` — pauses the graph for approve/revise | Human |
| `final_response_agent` | Polished final plan, or a revision if not approved | LLM |

### Guardrail

`supervisor_agent` first asks the LLM whether the request is a valid travel-planning request and
expects strict JSON (`{"allowed": bool, "reason": str}`). If not allowed, it short-circuits with a
rejection message in `final_response`.

### Human-in-the-loop

`human_approval_agent` calls LangGraph's `interrupt()`. `app.invoke(...)` returns with an
`__interrupt__` key holding the draft; the Streamlit UI renders the approval form and resumes the
same `thread_id` with `Command(resume={"approved": ..., "feedback": ...})`.

### Files

| File | Role |
|---|---|
| [graph.py](graph.py) | Builds the `StateGraph`, routing, Postgres checkpointer |
| [agents.py](agents.py) | All eight node functions |
| [state.py](state.py) | `TravelState` TypedDict |
| [config.py](config.py) | Env loading and `get_llm()` (ChatGroq) |
| [mcp_client.py](mcp_client.py) | `MultiServerMCPClient` config + tool wrappers |
| [weather_mcp_server.py](weather_mcp_server.py) | Local FastMCP server over OpenWeatherMap |
| [frontend.py](frontend.py) | Streamlit UI |
| `aviationstack-mcp/` | Vendored [Pradumnasaraf/aviationstack-mcp](https://github.com/Pradumnasaraf/aviationstack-mcp) server |

---

## Prerequisites

**API keys** (all free tiers work):

- Groq — https://console.groq.com
- Tavily — https://www.tavily.com/
- AviationStack — https://aviationstack.com/
- OpenWeatherMap — https://openweathermap.org/

**Plus** PostgreSQL and Python 3.13

---

## Environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATION_STACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweathermap_api_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/langgraph_memory_demo
```

Optional:

```
GROQ_MODEL=llama-3.3-70b-versatile
```

Notes:

- The AviationStack variable is `AVIATION_STACK_API_KEY` (with the underscore) — that is the name
  both [config.py](config.py) and the MCP server read.
- If `DATABASE_URL` is unset, [graph.py](graph.py) compiles the graph **without** a checkpointer.
  The app still runs, but human-in-the-loop resume will not work, because resuming needs the
  interrupted thread to have been persisted.

---

## Run with Docker

Everything (app + Postgres) comes up with one command.

```bash
docker compose up --build
```

Then open http://localhost:8501

Before your first run, point `DATABASE_URL` in `.env` at the compose Postgres service — inside the
network the host is `postgres`, the port is `5432`, and the database created by
[docker-compose.yml](docker-compose.yml) is `langgraph_memory`:

```
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langgraph_memory
```

To stop:

```bash
docker compose down
```

Add `-v` to that command to also drop the `postgres_data` volume and wipe checkpointed threads.

The image installs the vendored `aviationstack-mcp` package, so no separate MCP setup is needed.

---


Example prompt:

```
Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs.
```

---

## Features

- Supervisor-routed multi-agent architecture on LangGraph
- LLM input guardrail on every request
- Human-in-the-loop approval via `interrupt()` / `Command(resume=...)`
- Three MCP integrations: Tavily (HTTP), AviationStack (stdio), Weather (stdio, local FastMCP)
- PostgreSQL checkpointing with resumable threads
- Streamlit web UI
- Docker Compose deployment


