
import asyncio
import websockets
import json
import os
import base64
import datetime
from dotenv import load_dotenv
from tools import tools_definition, list_calendar_events, check_availability, create_calendar_event

load_dotenv()

class RealtimeAgent:
    def __init__(self, audio_handler=None, on_message=None):
        self.url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-2025-08-28"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.audio_handler = audio_handler
        self.on_message = on_message
        self.websocket = None

    async def connect(self, modalities=None):
        print(f"Connecting to {self.url}...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        async with websockets.connect(self.url, additional_headers=headers) as websocket:
            self.websocket = websocket
            print("Connected to OpenAI Realtime API")
            
            # Update session with tools
            await self.update_session(modalities)
            
            # Start receiving messages
            await self.receive_loop()

    async def update_session(self, modalities=None):
        if modalities is None:
            modalities = ["text", "audio"]
        
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": modalities,
                "instructions": "You are a professional AI executive assistant for **Sanwal Khan**. Your job is to schedule meetings and manage his calendar. When checking availability, clearly state 'Sanwal Khan is available at [Time]'. Be polite, concise, and professional. Today is " + datetime.datetime.now().strftime("%Y-%m-%d") + ". The user is in Pakistan Standard Time (Asia/Karachi). Assume all times are PKT unless specified.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "tools": tools_definition,
                "tool_choice": "auto",
            }
        }
        await self.websocket.send(json.dumps(session_update))

    async def send_text(self, text):
        if self.websocket:
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            await self.websocket.send(json.dumps({"type": "response.create"}))

    async def receive_loop(self):
        async for message in self.websocket:
            try:
                data = json.loads(message)
                
                if self.on_message:
                    await self.on_message(data)

                event_type = data.get("type")
                
                # Default debug print for EVERYTHING except audio deltas (too spammy)
                # if event_type != "response.audio.delta":
                    # print(f"\n[DEBUG] Event: {event_type}")
                    # print(json.dumps(data, indent=2)) # Uncomment if needed for deep inspection

                if event_type == "error":
                    print(f"Error from OpenAI: {data}")

                if event_type == "response.text.delta":
                     print(data.get('delta'), end="", flush=True)

                if event_type == "response.audio.transcript.delta":
                     print(data.get('delta'), end="", flush=True)

                if event_type == "response.audio.delta":
                    if self.audio_handler:
                        audio_bytes = base64.b64decode(data["delta"])
                        self.audio_handler.play_audio(audio_bytes)
                
                elif event_type == "response.done":
                    # print(f"\n[DEBUG] RESPONSE DONE. Status: {data['response']['status']}")
                    if data['response']['status'] == 'failed':
                        print(json.dumps(data, indent=2))
                    else:
                        print() # Newline after streaming text
                    
                    # Check for tool calls
                    if "output" in data["response"] and data["response"]["output"]:
                         for item in data["response"]["output"]:
                             if item["type"] == "function_call":
                                 await self.handle_tool_call(item)
            except Exception as e:
                print(f"Error processing message: {e}")

    async def handle_tool_call(self, tool_call):
        name = tool_call["name"]
        args = json.loads(tool_call["arguments"])
        call_id = tool_call["call_id"]
        
        print(f"Tool call: {name} with args: {args}")
        
        result = "{}"
        if name == "list_calendar_events":
            result = list_calendar_events(**args)
        elif name == "check_availability":
            result = check_availability(**args)
        elif name == "create_calendar_event":
            result = create_calendar_event(**args)

        tool_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result
            }
        }
        await self.websocket.send(json.dumps(tool_output))
        
        # Trigger response after tool output
        await self.websocket.send(json.dumps({"type": "response.create"}))
