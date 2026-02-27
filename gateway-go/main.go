package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"strconv"

	pb "github.com/roopesharch/EchoSonic/gateway-go/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	conn, _ := grpc.Dial("127.0.0.1:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			return
		}

		r.ParseForm()
		speed, _ := strconv.ParseFloat(r.FormValue("speed"), 32)
		noise, _ := strconv.ParseFloat(r.FormValue("noise"), 32)

		_, err := client.Speak(context.Background(), &pb.SpeakRequest{
			Text:  r.FormValue("text"),
			Voice: r.FormValue("voice"),
			Speed: float32(speed),
			Noise: float32(noise),
		})

		if err != nil {
			w.WriteHeader(500)
			return
		}
		w.WriteHeader(200)
	})

	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")

		filePath := "../engine-python/output.wav"
		file, err := os.Open(filePath)
		if err != nil {
			http.Error(w, "File not found", 404)
			return
		}
		defer file.Close()

		// Get file info to tell the browser the exact size
		stat, _ := file.Stat()
		w.Header().Set("Content-Length", strconv.FormatInt(stat.Size(), 10))
		w.Header().Set("Content-Type", "audio/wav")
		w.Header().Set("Accept-Ranges", "bytes")

		http.ServeContent(w, r, "output.wav", stat.ModTime(), file)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
