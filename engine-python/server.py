import grpc
from concurrent import futures
import os
import wave
import voice_pb2
import voice_pb2_grpc
from piper.voice import PiperVoice 

# Memory cache for voices
VOICE_MODELS = {}

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Ensure we are looking for the 'low' version
        voice_file = request.voice.replace("-medium", "-low")
        model_path = os.path.join(base_path, voice_file)
        output_path = "/app/shared_output.wav"

        try:
            # Load into RAM if not already there
            if voice_file not in VOICE_MODELS:
                print(f"--- Loading {voice_file} into RAM ---")
                VOICE_MODELS[voice_file] = PiperVoice.load(model_path)
            
            voice = VOICE_MODELS[voice_file]

            # Synthesize directly (Much faster than subprocess)
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
    print("🚀 Fast Engine (Low-Quality Mode) Live...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()