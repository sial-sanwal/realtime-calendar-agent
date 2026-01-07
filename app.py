
import streamlit as st
import asyncio
import json
import os
from agent import RealtimeAgent
import tools  # Import tools to set credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Set page configuration
st.set_page_config(page_title="AI Calendar Agent", layout="wide")
st.title("📅 Realtime Calendar Agent")

# Sidebar for Configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. OpenAI API Key
    api_key_input = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY") or "")
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input

    st.divider()

    # 2. Google Calendar OAuth
    st.subheader("Google Integration")
    
    # We need a client_secrets.json for the web flow to work properly 
    # OR we can ask user for Client ID / Secret manually if file doesn't exist
    
    if "google_creds" not in st.session_state:
        st.write("Not Connected")
        
        # Check if we are in the middle of a redirect
        if "code" in st.query_params:
            code = st.query_params["code"]
            try:
                # Reconstruct flow to fetch token
                # client_secrets.json is required for this part in a real app
                # For this demo, we assume the user puts a 'client_secrets.json' in the root
                flow = Flow.from_client_secrets_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly'],
                    redirect_uri='http://localhost:8501'
                )
                flow.fetch_token(code=code)
                st.session_state.google_creds = flow.credentials
                st.success("Connected!")
                st.query_params.clear() # Clean URL
                st.rerun()
            except Exception as e:
                st.error(f"Auth failed: {e}")
        else:
            if st.button("Connect Google Calendar"):
                try:
                    flow = Flow.from_client_secrets_file(
                        'credentials.json',
                        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly'],
                        redirect_uri='http://localhost:8501'
                    )
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.markdown(f"[>> Click here to Login with Google <<]({auth_url})")
                except FileNotFoundError:
                    st.error("Missing ' credentials.json'. Please add it to project root.")
    else:
        st.success("✅ Connected to Google Calendar")
        # Inject credentials into tools
        tools.set_user_credentials(st.session_state.google_creds)
        
        if st.button("Logout"):
            del st.session_state.google_creds
            st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

async def run_chat_cycle(user_input):
    # Queue for passing messages from agent to UI
    response_queue = asyncio.Queue()
    
    async def on_message_handler(data):
        await response_queue.put(data)

    agent = RealtimeAgent(audio_handler=None, on_message=on_message_handler)
    
    # Start connection in a background task
    connect_task = asyncio.create_task(agent.connect(modalities=["text"]))
    
    # Wait for websocket to be ready
    while agent.websocket is None:
        await asyncio.sleep(0.1)

    # Restore conversation context from history
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        
        # Map Streamlit roles to OpenAI Realtime roles
        # 'user' -> 'user', 'assistant' -> 'assistant'
        
        item_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": role,
                "content": [{"type": "input_text", "text": content}]
            }
        }
        await agent.websocket.send(json.dumps(item_event))

    # Send User Message
    msg = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": user_input}]
        }
    }
    await agent.websocket.send(json.dumps(msg))
    await agent.websocket.send(json.dumps({"type": "response.create"}))

    # UI Update Loop
    full_response = ""
    placeholder = st.empty()
    
    try:
        while True:
            # Wait for next event
            data = await response_queue.get()
            event_type = data.get("type")

            if event_type == "response.text.delta":
                delta = data.get("delta", "")
                full_response += delta
                placeholder.markdown(full_response + "▌")
            
            elif event_type == "response.audio.transcript.delta":
                 delta = data.get("delta", "")
                 full_response += delta
                 placeholder.markdown(full_response + "▌")
            
            elif event_type == "response.done":
                # Check for tool calls inside the response
                if "output" in data["response"] and data["response"]["output"]:
                     # If tools were called, the agent.py logic handles usage.
                     # But we need to keep listening for the NEXT response logic.
                     # NOTE: 'response.done' implies THIS response is done. 
                     # If tool handled, agent sends tx/response.create, so more events come.
                     # We only break if it's a final answer.
                     
                     is_tool_call = any(item['type'] == 'function_call' for item in data['response'].get('output', []))
                     if not is_tool_call:
                         break
                else:
                     # No output usually means audio only or weird state, but if status is completed:
                     if data['response']['status'] == 'completed':
                         break
            
            elif event_type == "item.created" and data["item"]["type"] == "function_call_output":
                # Tool output posted, expect new response soon
                with st.spinner("Consulting calendar..."):
                    pass

    finally:
        # Cleanup
        if agent.websocket:
            await agent.websocket.close()
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    return full_response

# Handle Input
if prompt := st.chat_input("Ask to book a meeting..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response_text = asyncio.run(run_chat_cycle(prompt))
        # st.markdown(response_text) # Removed to prevent duplicate
    
    st.session_state.messages.append({"role": "assistant", "content": response_text})
