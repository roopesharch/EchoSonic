import grpc
from concurrent import futures
import subprocess
import os
import voice_pb2
import voice_pb2_grpc

class VoiceService(voice_pb2_grpc.VoiceServiceServicer):
    def Speak(self, request, context):
        base_path = os.path.dirname(os.path.abspath(__file__))
        piper_bin = os.path.join(base_path, "piper", "piper")
        model_path = os.path.join(base_path, request.voice)
        output_path = os.path.join(base_path, "output.wav")

        # Command to run Piper
        command = [
            piper_bin,
            "--model", model_path,
            "--length_scale", str(1.0 / request.speed),
            "--noise_scale", str(request.noise),
            "--output_file", output_path
        ]
        
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE)
            process.communicate(input=request.text.encode('utf-8'))
            return voice_pb2.SpeakResponse(success=True)
        except Exception as e:
            print(f"Error generating audio: {e}")
            return voice_pb2.SpeakResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_pb2_grpc.add_VoiceServiceServicer_to_server(VoiceService(), server)
    server.add_insecure_port('[::]:50051')
    print("AI Engine listening on 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()