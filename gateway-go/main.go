package main

import (
	"context"
	"net/http"
	"os"
	"strconv"
	"time"

	pb "github.com/roopesharch/EchoSonic/gateway-go/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	conn, _ := grpc.Dial("127.0.0.1:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	// Route 1: Home/Health Check
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("🚀 EchoSonic API is running on Branch 01"))
	})

	// Route 2: Speak (Trigger AI)
	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			return
		}

		r.ParseForm()
		speed, _ := strconv.ParseFloat(r.FormValue("speed"), 32)

		_, _ = client.Speak(context.Background(), &pb.SpeakRequest{
			Text:  r.FormValue("text"),
			Voice: r.FormValue("voice"),
			Speed: float32(speed),
			Noise: 0.667,
		})
		w.WriteHeader(200)
	})

	// Route 3: Listen (Stream Audio)
	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		filePath := "/app/shared_output.wav"

		// SYNC LOCK: Wait for file to have actual audio data
		for i := 0; i < 10; i++ {
			info, err := os.Stat(filePath)
			if err == nil && info.Size() > 100 {
				break
			}
			time.Sleep(400 * time.Millisecond)
		}

		file, err := os.Open(filePath)
		if err != nil {
			http.Error(w, "File busy or not found", 404)
			return
		}
		defer file.Close()

		info, _ := file.Stat()
		w.Header().Set("Content-Type", "audio/wav")
		w.Header().Set("Content-Length", strconv.FormatInt(info.Size(), 10))
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")

		http.ServeContent(w, r, "output.wav", time.Now(), file)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.ListenAndServe(":"+port, nil)
}
