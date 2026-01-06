
import asyncio
import signal
import sys
from agent import RealtimeAgent


async def chat_loop(agent):
    print("Start chatting (type 'quit' to exit):")
    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            await agent.send_text(user_input)
        except EOFError:
            break


async def main():
    agent = RealtimeAgent(audio_handler=None)
    
    # Start connection in background w/ text only
    connect_task = asyncio.create_task(agent.connect(modalities=["text"]))
    
    # Wait a bit for connection
    await asyncio.sleep(2)
    
    # Start chat loop
    try:
        await chat_loop(agent)
    except asyncio.CancelledError:
        pass
    finally:
        print("Closing connection...")
        if agent.websocket:
            await agent.websocket.close()
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
