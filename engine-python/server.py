import grpc
from concurrent import futures
import os
import wave
import voice_pb2
import voice_pb2_grpc
from piper.voice import PiperVoice 

# Memory cache for voices to keep them "warm"
VOICE_MODELS = {}

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, request.voice)
        output_path = "/app/shared_output.wav"

        try:
            # Load into RAM if not already there for speed
            if request.voice not in VOICE_MODELS:
                print(f"--- 🧠 Loading {request.voice} into RAM ---")
                VOICE_MODELS[request.voice] = PiperVoice.load(model_path)
            
            voice = VOICE_MODELS[request.voice]

            # Delete old file to prevent the browser from playing old data
            if os.path.exists(output_path):
                os.remove(output_path)

            # Synthesize
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(request.text, wav_file)
            
            # CRITICAL: Force the OS to flush the file to disk
            os.sync() 
            
            file_size = os.path.getsize(output_path)
            print(f"✅ Python finalized {file_size} bytes for {request.voice}")
            
            return voice_pb2.SpeakResponse(success=True)
        except Exception as e:
            print(f"🔥 Python Error: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Speed-Optimized Engine (Branch 01) Live...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()