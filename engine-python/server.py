import grpc
from concurrent import futures
import subprocess
import os
import voice_pb2
import voice_pb2_grpc

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        # 1. Setup paths
        # Look for piper in ./piper/piper (from the tar extract)
        piper_bin = os.path.abspath("./piper/piper")
        model_path = os.path.abspath(f"./{request.voice if request.voice.endswith('.onnx') else 'en_US-lessac-medium.onnx'}")
        output_path = os.path.abspath("output.wav")

        # 2. CACHE BUSTING: Remove old file so you don't hear old text
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

        # 3. Build the command
        # Use length_scale = 1.0 / speed (Higher speed = lower scale)
        length_scale = str(1.0 / request.speed) if request.speed > 0 else "1.0"
        
        command = [
            piper_bin,
            "--model", model_path,
            "--length_scale", length_scale,
            "--noise_scale", str(request.noise),
            "--output_file", output_path
        ]

        try:
            print(f"🎙️ Generating AI Voice: '{request.text[:50]}...'")
            # We use a context manager to ensure stdin is closed properly
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=request.text.encode('utf-8'))

            if process.returncode == 0 and os.path.exists(output_path):
                print("✅ Audio generated successfully.")
                return voice_pb2.SpeakResponse(success=True)
            else:
                print(f"❌ Piper Error: {stderr.decode()}")
                return voice_pb2.SpeakResponse(success=False)
        except Exception as e:
            print(f"❌ Python System Error: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("🤖 Python AI Engine (Pro) ready on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()