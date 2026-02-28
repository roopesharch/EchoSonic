import grpc
from concurrent import futures
import subprocess
import os
import voice_pb2
import voice_pb2_grpc

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        # Using absolute paths to avoid 'File Not Found' errors on Render
        base_path = os.path.dirname(os.path.abspath(__file__))
        piper_bin = os.path.join(base_path, "piper", "piper")
        model_path = os.path.join(base_path, request.voice)
        
        # We save it to the root of /app so Go can find it easily
        output_path = "/app/shared_output.wav"

        command = [
            piper_bin,
            "--model", model_path,
            "--length_scale", str(1.0 / request.speed),
            "--noise_scale", str(request.noise),
            "--output_file", output_path
        ]
        
        try:
            # Ensure any old file is gone before writing new one
            if os.path.exists(output_path):
                os.remove(output_path)
                
            process = subprocess.Popen(command, stdin=subprocess.PIPE)
            process.communicate(input=request.text.encode('utf-8'))
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return voice_pb2.SpeakResponse(success=True)
            return voice_pb2.SpeakResponse(success=False)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()