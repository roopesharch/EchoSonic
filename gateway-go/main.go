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

	// Home route
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("🚀 EchoSonic API is Live"))
	})

	// Speak route
	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			return
		}

		r.ParseForm()
		speed, _ := strconv.ParseFloat(r.FormValue("speed"), 32)

		// Blocks until Python confirms the file is written
		resp, err := client.Speak(context.Background(), &pb.SpeakRequest{
			Text:  r.FormValue("text"),
			Voice: r.FormValue("voice"),
			Speed: float32(speed),
		})

		if err != nil || !resp.Success {
			w.WriteHeader(500)
			return
		}
		w.WriteHeader(200)
	})

	// Listen route with File Verification
	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		filePath := "/app/shared_output.wav"

		var finalInfo os.FileInfo
		// Check the file up to 15 times (approx 7 seconds)
		for i := 0; i < 15; i++ {
			info, err := os.Stat(filePath)
			if err == nil && info.Size() > 100 {
				finalInfo = info
				break
			}
			time.Sleep(500 * time.Millisecond)
		}

		if finalInfo == nil {
			http.Error(w, "File not ready or empty", 404)
			return
		}

		file, _ := os.Open(filePath)
		defer file.Close()

		w.Header().Set("Content-Type", "audio/wav")
		w.Header().Set("Content-Length", strconv.FormatInt(finalInfo.Size(), 10))
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")

		http.ServeContent(w, r, "output.wav", time.Now(), file)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.ListenAndServe(":"+port, nil)
}
