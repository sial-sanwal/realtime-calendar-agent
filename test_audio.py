
import pyaudio
import time

def test_audio():
    p = pyaudio.PyAudio()
    
    print("Default Input Device Info:")
    try:
        print(p.get_default_input_device_info())
    except Exception as e:
        print(f"Error getting input device: {e}")

    print("\nDefault Output Device Info:")
    try:
        print(p.get_default_output_device_info())
    except Exception as e:
        print(f"Error getting output device: {e}")

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000
    CHUNK = 1024
    RECORD_SECONDS = 3

    print("\nAttempting to record for 3 seconds...")
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
            
        print("Recording finished.")
        stream.stop_stream()
        stream.close()
        
        print("Attempting to play back...")
        stream_out = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True)
        
        for frame in frames:
            stream_out.write(frame)
            
        stream_out.stop_stream()
        stream_out.close()
        print("Playback finished.")
        
    except Exception as e:
        print(f"CRITICAL ERROR during audio test: {e}")
        import traceback
        traceback.print_exc()

    p.terminate()

if __name__ == "__main__":
    test_audio()
