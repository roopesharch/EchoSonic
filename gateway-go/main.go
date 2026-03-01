package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"

	pb "github.com/roopesharch/EchoSonic/gateway-go/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	conn, _ := grpc.Dial("127.0.0.1:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	baseDir := "/workspaces/EchoSonic"
	if _, err := os.Stat(baseDir); err != nil {
		baseDir = "/app"
	}
	sharedFilePath := filepath.Join(baseDir, "shared_output.wav")
	docsPath := filepath.Join(baseDir, "docs")

	http.Handle("/", http.FileServer(http.Dir(docsPath)))

	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		r.ParseForm()
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()

		resp, err := client.Speak(ctx, &pb.SpeakRequest{
			Text:  r.FormValue("text"),
			Voice: r.FormValue("voice"),
		})

		if err != nil || !resp.Success {
			http.Error(w, "Engine error", 500)
			return
		}
		w.WriteHeader(200)
	})

	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		time.Sleep(300 * time.Millisecond)
		if info, err := os.Stat(sharedFilePath); err == nil && info.Size() > 44 {
			file, _ := os.Open(sharedFilePath)
			defer file.Close()
			w.Header().Set("Content-Type", "audio/wav")
			http.ServeContent(w, r, "output.wav", time.Now(), file)
			return
		}
		http.Error(w, "File not ready", 404)
	})

	fmt.Println("🚀 Gateway Running on :8080")
	http.ListenAndServe(":8080", nil)
}
