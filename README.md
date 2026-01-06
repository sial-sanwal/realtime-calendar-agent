
# 📅 AI Realtime Calendar Agent

This project implements a **Realtime AI Voice & Chat Agent** capable of checking availability and booking meetings on Google Calendar in real-time. It uses **OpenAI's Realtime API** for sub-second voice/text interaction and **Google Calendar API** for scheduling.

## 🚀 How It Works

1.  **User Interaction**: You talk (Voice) or type (Chat) to the agent.
2.  **OpenAI Realtime API**: The agent processes the input immediately using the `gpt-realtime-2025-08-28` model.
3.  **Tool Calling**: If you ask to "book a meeting", the model decides to call a specific tool function (e.g., `check_availability` or `create_calendar_event`).
4.  **Google Calendar API**: The system executes the tool, querying or updating your live Google Calendar.
5.  **Response**: The result is sent back to the model, which generates a natural language confirmation (e.g., "Done, Sanwal Khan's meeting is booked for 5 PM").

## 🛠️ Tech Stack & APIs

-   **LLM Model**: `gpt-realtime-2025-08-28` (OpenAI Realtime API via WebSockets).
-   **Calendar**: Google Calendar API (v3).
-   **Audio**: `PyAudio` for microphone input and speaker output.
-   **Frontend**: `Streamlit` for the Chat UI (`app.py`).
-   **Backend Logic**: Python `asyncio` and `websockets`.

## 📂 Key Files

-   `agent.py`: Manages the WebSocket connection to OpenAI and handles tool execution.
-   `tools.py`: Contains the Google Calendar functions (`check_availability`, `create_calendar_event`).
-   `app.py`: The Streamlit web interface for chat.
-   `main.py`: The Voice-only terminal client.
-   `audio.py`: Handles audio recording and playback.

## 🇵🇰 Timezone Configuration

The agent is currently hardcoded to **Pakistan Standard Time (Asia/Karachi)**.
-   **Prompt**: The agent knows it is an assistant for "Sanwal Khan" in PKT.
-   **Tools**: Calendar events are created with `timeZone: 'Asia/Karachi'`.

## 🚢 Moving to Production

If you want to deploy this app for a broad audience or clients, consider the following changes:

### 1. Authentication (OAuth)
-   **Current**: Uses a local `credentials.json` and a user-interactive flow that opens a browser on the server.
-   **Production**: You must implement a proper OAuth2 Web Flow. Users should visit your website, log in with Google, and your server should save their `refresh_token` securely in a database (PostgreSQL/MongoDB) associated with their user ID.

### 2. Environment Variables
-   Never store keys (like `OPENAI_API_KEY`) in code. Use a Secret Manager (AWS Secrets Manager, Google Secret Manager) or securely injected environment variables in your deployment platform.

### 3. Dynamic Timezones
-   **Current**: Hardcoded to `Asia/Karachi`.
-   **Production**: Detect the user's timezone from the browser or ask them to set it in their profile. Pass this timezone dynamically to the `tools.py` functions so bookings happen in *their* local time.

### 4. Deployment
-   **Containerization**: Dockerize the application to ensure it runs consistently on any server (AWS EC2, Google Cloud Run, Heroku).
-   **HTTPS/WSS**: Ensure all WebSocket and HTTP connections are checking over SSL/TLS for security.

### 5. Scalability
-   The current `app.py` uses `asyncio` but Streamlit is not optimized for thousands of concurrent WebSocket connections. For high scale, consider a separate backend (FastAPI/Node.js) handling the WebSockets and a frontend (React/Next.js) talking to it.
