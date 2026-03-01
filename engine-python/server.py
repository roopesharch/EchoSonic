import grpc
from concurrent import futures
import os
import wave
import voice_pb2
import voice_pb2_grpc
from piper.voice import PiperVoice 

# Memory cache for voices to prevent reloading from disk
VOICE_MODELS = {}

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, request.voice)
        output_path = "/app/shared_output.wav"

        if not os.path.exists(model_path):
            print(f"❌ Error: Model {request.voice} not found")
            return voice_pb2.SpeakResponse(success=False)

        try:
            # Load into RAM if not already there
            if request.voice not in VOICE_MODELS:
                print(f"--- 🧠 Loading {request.voice} into RAM ---")
                VOICE_MODELS[request.voice] = PiperVoice.load(model_path)
            
            voice = VOICE_MODELS[request.voice]

            # 1. Clear old file
            if os.path.exists(output_path):
                os.remove(output_path)

            # 2. Synthesize to WAV
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(request.text, wav_file)
            
            # 3. Final Check
            size = os.path.getsize(output_path)
            print(f"✅ Generated: {size} bytes for {request.voice}")
            
            return voice_pb2.SpeakResponse(success=True)
        except Exception as e:
            print(f"🔥 Python Error: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Fast Engine (Branch 01) Listening on 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()