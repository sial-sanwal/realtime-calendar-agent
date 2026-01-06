
import asyncio
import signal
import sys
from audio import AudioHandler
from agent import RealtimeAgent

async def main():
    stop_event = asyncio.Event()

    def signal_handler():
        print('\nStopping...')
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    audio = AudioHandler()
    agent = RealtimeAgent(audio)
    
    # Callback to send audio from mic to agent
    async def audio_callback(data):
        if not stop_event.is_set():
             await agent.send_audio(data)

    audio.start_input_stream(loop, audio_callback)
    audio.start_output_stream()

    connect_task = asyncio.create_task(agent.connect())

    try:
        await stop_event.wait()
    finally:
        print("Cleaning up...")
        audio.stop()
        if agent.websocket:
            await agent.websocket.close()
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
