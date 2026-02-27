package main

import (
	"context"
	"fmt"
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

	// Route to handle speech generation
	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		// ALLOW GITHUB PAGES TO ACCESS THIS
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

	// Route to serve the audio file
	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Content-Type", "audio/wav")
		http.ServeFile(w, r, "../engine-python/output.wav")
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	fmt.Println("Gateway live on port", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
