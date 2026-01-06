
import pyaudio
import base64
import asyncio
import queue

class AudioHandler:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk = 1024
        
        self.stream_out = None
        self.input_queue = queue.Queue()
        self.is_recording = False

    def start_input_stream(self, loop, audio_callback):
        self.is_recording = True
        
        def record_loop():
            stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            print("Microphone stream started.")
            while self.is_recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    b64_data = base64.b64encode(data).decode('utf-8')
                    # Schedule the callback in the main event loop
                    asyncio.run_coroutine_threadsafe(audio_callback(b64_data), loop)
                except Exception as e:
                    print(f"Error recording: {e}")
                    break
            stream.stop_stream()
            stream.close()
            print("Microphone stream stopped.")

        # Run recording in a separate thread to avoid blocking asyncio
        import threading
        self.record_thread = threading.Thread(target=record_loop)
        self.record_thread.start()

    def start_output_stream(self):
        self.stream_out = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True
        )

    def play_audio(self, audio_data: bytes):
        if self.stream_out:
            try:
                self.stream_out.write(audio_data)
            except Exception as e:
                print(f"Error playing audio: {e}")

    def stop(self):
        self.is_recording = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join(timeout=1)
            
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
        self.p.terminate()
