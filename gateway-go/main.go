package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	pb "github.com/roopesharch/EchoSonic/gateway-go/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	conn, err := grpc.Dial("127.0.0.1:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Fail to dial: %v", err)
	}
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	// Route 1: The Main UI
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, `
			<html>
			<body style="font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #f0f2f5; padding: 50px;">
				<h1>🎙️ EchoSonic AI</h1>
				<form action="/speak" method="GET">
					<input type="text" name="text" style="padding: 15px; width: 400px; border-radius: 5px; border: 1px solid #ccc;" placeholder="Type something...">
					<button type="submit" style="padding: 15px 25px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Generate Speech</button>
				</form>
			</body>
			</html>
		`)
	})

	// Route 2: The Logic (Triggers Python)
	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		text := r.URL.Query().Get("text")
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*30)
		defer cancel()

		_, err := client.Speak(ctx, &pb.SpeakRequest{Text: text})
		if err != nil {
			http.Error(w, "AI Engine Timeout - Try a shorter sentence.", 504)
			return
		}

		// Success Page with Player and Direct Link
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, `
			<html>
			<body style="font-family: sans-serif; text-align: center; padding: 50px; background: #f0f2f5;">
				<h2>✅ Speech Ready</h2>
				<audio controls autoplay style="width: 500px;">
					<source src="/listen" type="audio/wav">
				</audio>
				<br><br>
				<a href="/listen" target="_blank" style="font-size: 20px; color: #007bff;">Click here to open raw audio file</a>
				<br><br>
				<a href="/">⬅️ Back to home</a>
			</body>
			</html>
		`)
	})

	// Route 3: The Audio Stream
	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "audio/wav")
		// This path must point to where Python saves the file
		http.ServeFile(w, r, "../engine-python/output.wav")
	})

	fmt.Println("🌐 EchoSonic UI Live on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
