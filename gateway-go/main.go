package main

import (
	"context"
	"io"
	"log"
	"os"
	"os/exec"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "gateway-go/pb"
)

func main() {
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("❌ Connection failed: %v", err)
	}
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	// 1. Check if story.txt is actually readable
	content, err := os.ReadFile("story.txt")
	if err != nil {
		log.Fatalf("❌ Could not read story.txt: %v", err)
	}
	if len(content) == 0 {
		log.Fatalf("❌ story.txt is EMPTY! Put some text in it first.")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	log.Println("📖 Sending story.txt to Offline AI...")
	stream, err := client.GenerateSpeech(ctx, &pb.SpeechRequest{
		Text: string(content),
	})
	if err != nil {
		log.Fatalf("❌ Stream error: %v", err)
	}

	tempFile := "audiobook.wav"
	outFile, _ := os.Create(tempFile)

	var totalBytes int64
	for {
		res, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("❌ Receive error: %v", err)
		}
		n, _ := outFile.Write(res.GetAudioChunk())
		totalBytes += int64(n)
	}
	outFile.Close()

	// 2. Debug: Check if the file actually has audio data
	if totalBytes < 100 {
		log.Fatalf("❌ The AI generated an empty file (%d bytes). Check the Python logs!", totalBytes)
	}

	log.Printf("🔊 Playing %d bytes of offline audio...", totalBytes)
	exec.Command("afplay", tempFile).Run()

	os.Remove(tempFile)
	log.Println("✅ Done!")
}