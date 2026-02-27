import grpc
from concurrent import futures
import voice_pb2
import voice_pb2_grpc
import io
import wave
import os
import sys
from piper.voice import PiperVoice

# 1. Force the absolute path to the model
# This ensures Python finds it even if you are in a different subfolder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "en_US-lessac-medium.onnx")
config_path = os.path.join(BASE_DIR, "en_US-lessac-medium.onnx.json")

print(f"🔍 Looking for model at: {model_path}")

if not os.path.exists(model_path):
    print(f"❌ FATAL ERROR: Model file not found!")
    sys.exit(1)

try:
    voice = PiperVoice.load(model_path, config_path)
    print("🧠 AI Voice Brain loaded successfully!")
except Exception as e:
    print(f"❌ FATAL ERROR loading Piper: {e}")
    sys.exit(1)

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def GenerateSpeech(self, request, context):
        text = request.text.strip()
        if not text:
            print("⚠️ Empty text received.")
            return

        print(f"🧬 Synthesizing: '{text[:30]}...'")
        
        audio_stream = io.BytesIO()
        
        try:
            with wave.open(audio_stream, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                
                # The actual "Speaking" part
                voice.synthesize(text, wav_file)
            
            audio_size = audio_stream.tell()
            print(f"📦 Audio generated: {audio_size} bytes")
            
            if audio_size <= 44:
                print("⚠️ Warning: Piper generated no audio content!")

            audio_stream.seek(0)
            while True:
                chunk = audio_stream.read(4096)
                if not chunk:
                    break
                yield voice_pb2.SpeechResponse(audio_chunk=chunk)
        
        except Exception as e:
            print(f"❌ Synthesis Error: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 OFFLINE SERVER READY ON 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()