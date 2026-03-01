import grpc
from concurrent import futures
import os
import wave
import threading
import voice_pb2
import voice_pb2_grpc
from piper.voice import PiperVoice 

VOICE_MODELS = {}
synth_lock = threading.Lock()

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_dir = "/workspaces/EchoSonic"
        if not os.path.exists(base_dir): base_dir = "/app"
        
        model_path = os.path.join(base_dir, "engine-python", request.voice)
        final_output_path = os.path.join(base_dir, "shared_output.wav")

        print(f"\n--- 🎙️ Synthesis: '{request.text[:30]}...' ---")

        with synth_lock:
            try:
                if request.voice not in VOICE_MODELS:
                    VOICE_MODELS[request.voice] = PiperVoice.load(model_path)
                
                voice = VOICE_MODELS[request.voice]

                if os.path.exists(final_output_path):
                    os.remove(final_output_path)

                with wave.open(final_output_path, "wb") as wav_file:
                    # Piper defaults
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    rate = getattr(voice.config, 'sample_rate', 22050)
                    wav_file.setframerate(rate)
                    
                    print("DEBUG: Extracting audio_int16_bytes...")
                    for chunk in voice.synthesize(request.text):
                        # SUCCESS: Found the attribute via your debug log!
                        if hasattr(chunk, 'audio_int16_bytes'):
                            wav_file.writeframes(chunk.audio_int16_bytes)
                        elif hasattr(chunk, 'audio'):
                            wav_file.writeframes(chunk.audio)
                        else:
                            # Fallback to direct bytes if it's already raw
                            wav_file.writeframes(bytes(chunk))

                size = os.path.getsize(final_output_path)
                print(f"✅ SUCCESS: {size} bytes written.")
                return voice_pb2.SpeakResponse(success=(size > 44))

            except Exception as e:
                print(f"🔥 ENGINE ERROR: {str(e)}")
                return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Python Engine (v2) Ready on 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()