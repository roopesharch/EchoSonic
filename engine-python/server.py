import grpc
from concurrent import futures
import voice_pb2
import voice_pb2_grpc
import os
import subprocess
import time

class VoiceServicer(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        print(f"🎙️ gRPC Call: {request.text}")
        output_path = "output.wav"
        model_path = "en_US-lessac-medium.onnx"

        # 1. Clean up old file
        if os.path.exists(output_path):
            os.remove(output_path)

        try:
            # 2. Use the Command Line tool directly (This is what worked for you!)
            # We "pipe" the text into the piper command
            command = f'echo "{request.text}" | piper --model {model_path} --output_file {output_path}'
            subprocess.run(command, shell=True, check=True)

            # 3. Verify it worked
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                print(f"✅ Success: {size} bytes generated.")
                return voice_pb2.SpeakResponse(success=True, message=f"Generated {size} bytes")
            
            return voice_pb2.SpeakResponse(success=False, message="File not created")

        except Exception as e:
            print(f"❌ Subprocess error: {e}")
            return voice_pb2.SpeakResponse(success=False, message=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceServicer(), server)
    server.add_insecure_port('127.0.0.1:50051')
    print("🚀 BULLETPROOF SERVER ACTIVE on 127.0.0.1:50051")
    server.start()
    server.wait_for_termination() 

if __name__ == '__main__':
    serve()
    