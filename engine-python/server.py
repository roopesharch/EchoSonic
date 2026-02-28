import grpc
from concurrent import futures
import os
import wave
import voice_pb2
import voice_pb2_grpc
# NEW: Import the piper library directly
from piper.voice import PiperVoice 

# Global Cache: Keeps the model "warm" in memory
VOICE_MODELS = {}

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, request.voice)
        output_path = "/app/shared_output.wav"

        try:
            # PERFORMANCE HACK: Only load from disk if not already in RAM
            if request.voice not in VOICE_MODELS:
                print(f"--- Loading model {request.voice} into RAM ---")
                VOICE_MODELS[request.voice] = PiperVoice.load(model_path)
            
            voice = VOICE_MODELS[request.voice]

            # Direct synthesis (3-5x faster than subprocess)
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(request.text, wav_file)
            
            return voice_pb2.SpeakResponse(success=True)
        except Exception as e:
            print(f"Synthesis Error: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Fast AI Engine (Warm Model) Listening...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()