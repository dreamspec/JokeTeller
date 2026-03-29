# JokeTeller

JokeTeller is a local-first chat app with a FastAPI backend and a React + Vite frontend. It talks to a model already running in LM Studio through LM Studio's OpenAI-compatible local HTTP API, so the browser never talks to the model directly.

## What changed

- The backend API stays mostly the same: `GET /health`, `GET /status`, `POST /chat`, and `POST /chat/stream`
- The old Streamlit UI has been replaced with a proper React frontend
- The backend now includes CORS for local frontend development on Vite's local ports

## Features

- Playful local AI chat for jokes, banter, and normal conversation
- Streaming replies with progressive rendering
- Non-streaming fallback
- Left-side tuning panel for model, temperature, max tokens, top_p, prompt, and answer style
- Joke style selector, quick-action prompts, and preserved local chat history
- Backend status and LM Studio reachability checks

## Project layout

- `backend/`: FastAPI app and LM Studio integration
- `frontend/`: React + Vite + TypeScript app
- `.env`: shared local configuration for backend and frontend

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- LM Studio running locally on your Mac
- A model loaded in LM Studio
- LM Studio local server enabled

## Setup

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Update `.env` if needed:

- `LM_STUDIO_BASE_URL`: local LM Studio server, usually `http://127.0.0.1:1234`
- `LM_STUDIO_DEFAULT_MODEL`: optional; leave blank to auto-pick the first loaded model
- `LM_STUDIO_TIMEOUT_SECONDS`: request timeout for LM Studio calls
- `BACKEND_CORS_ORIGINS`: comma-separated allowed frontend origins for local browser use
- `VITE_API_BASE_URL`: backend URL used by the React app

3. Create and activate a Python virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

4. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

5. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Run locally

Open two terminals in the project root.

Terminal 1, start the backend:

```bash
cd /Users/yashrgx/Projects/JokeTeller
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, start the frontend:

```bash
cd /Users/yashrgx/Projects/JokeTeller/frontend
npm run dev
```

Then open:

- Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Backend docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API endpoints

- `GET /health`
- `GET /status`
- `POST /chat`
- `POST /chat/stream`

## LM Studio notes

- The backend normalizes `LM_STUDIO_BASE_URL`, so both `http://127.0.0.1:1234` and `http://127.0.0.1:1234/v1` work
- The backend uses the OpenAI-compatible local endpoints:
  - `/v1/models`
  - `/v1/chat/completions`
- If `LM_STUDIO_DEFAULT_MODEL` is blank, JokeTeller will use the first loaded model LM Studio exposes

## Frontend notes

- The React app persists settings and chat history in `localStorage`
- Streaming is handled through a browser fetch stream that parses backend SSE events
- The browser only talks to FastAPI, never to LM Studio directly

## Troubleshooting

### The browser cannot reach the backend

- Make sure FastAPI is running on `http://127.0.0.1:8000`
- Confirm `VITE_API_BASE_URL` matches the backend URL
- Confirm `BACKEND_CORS_ORIGINS` includes your frontend origin

### Backend is reachable but LM Studio is not

- Make sure LM Studio is open
- Make sure the local server is enabled
- Confirm `LM_STUDIO_BASE_URL` points to the correct local port

### Invalid model name

- Leave the model field blank to auto-pick the first loaded model
- Or use one of the model IDs shown in the frontend status panel

### Streaming feels slow

- Lower `max_tokens`
- Lower `temperature`
- Try a lighter local model
- Toggle streaming off to confirm the fallback path still works

## Manual smoke test

1. Open `http://127.0.0.1:8000/health` and confirm the backend reports `ok`.
2. Open `http://127.0.0.1:8000/status` and confirm LM Studio reachability is accurate.
3. Open the React app and confirm the status cards update correctly.
4. Send a normal message and confirm you get a response.
5. Keep streaming on and confirm the reply renders progressively.
6. Turn streaming off and confirm the non-streaming fallback still works.
7. Change joke style and confirm the flavor changes.
8. Change the left-pane temperature slider and confirm generation behavior changes.
9. Enter an invalid model name and confirm the UI shows a readable error.
10. Refresh the page and confirm chat history persists locally.
