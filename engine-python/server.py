import grpc
from concurrent import futures
import os
import wave
import voice_pb2
import voice_pb2_grpc
from piper.voice import PiperVoice 

# Global Cache: Keeps the model in RAM for high speed
VOICE_MODELS = {}

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, request.voice)
        output_path = "/app/shared_output.wav"

        try:
            # Load into RAM if not already there
            if request.voice not in VOICE_MODELS:
                print(f"--- 🧠 Loading {request.voice} into RAM ---")
                VOICE_MODELS[request.voice] = PiperVoice.load(model_path)
            
            voice = VOICE_MODELS[request.voice]

            # Clear old file to prevent race conditions
            if os.path.exists(output_path):
                os.remove(output_path)

            # Synthesize and close properly
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(request.text, wav_file)
            
            # CRITICAL: Force the Linux filesystem to sync data to disk
            os.sync() 
            
            size = os.path.getsize(output_path)
            print(f"✅ Python finalized {size} bytes")
            return voice_pb2.SpeakResponse(success=True)

        except Exception as e:
            print(f"🔥 Python Error: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    # Use a small pool to prevent Render from running out of memory
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Fast AI Engine (Branch 01) Live...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()