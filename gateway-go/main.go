package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	pb "github.com/roopesharch/EchoSonic/gateway-go/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	// Connect to the Python AI Engine
	conn, err := grpc.Dial("127.0.0.1:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Fail to dial AI Engine: %v", err)
	}
	defer conn.Close()
	client := pb.NewVoiceServiceClient(conn)

	// Route 1: The Main UI
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, `
			<html>
			<head>
				<title>EchoSonic Pro</title>
				<style>
					body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 40px; color: #1c1e21; }
					.card { background: white; max-width: 700px; margin: auto; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
					h1 { color: #1877f2; margin-bottom: 25px; }
					textarea { width: 100%%; padding: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; margin-bottom: 20px; resize: vertical; }
					.control-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
					label { font-weight: bold; display: block; margin-bottom: 8px; color: #4b4f56; }
					select, input[type=range] { width: 100%%; }
					button { width: 100%%; padding: 16px; background: #1877f2; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
					button:hover { background: #166fe5; }
					.hint { font-size: 12px; color: #606770; margin-top: 5px; }
				</style>
			</head>
			<body>
				<div class="card">
					<h1>🎙️ EchoSonic Pro</h1>
					<form action="/speak" method="POST">
						<label>Input Text (AI Engine supports up to 3,000 chars)</label>
						<textarea name="text" rows="6" maxlength="3000" placeholder="Type or paste your text here..."></textarea>
						
						<div class="control-row">
							<div>
								<label>Voice Model</label>
								<select name="voice">
									<option value="en_US-lessac-medium.onnx">Standard (Lessac)</option>
									<option value="en_US-amy-medium.onnx">Deep & Expressive (Amy)</option>
									<option value="en_US-kristin-medium.onnx">Soft & Calm (Kristin)</option>
								</select>
							</div>
							<div>
								<label>Speed (0.5x - 2.0x)</label>
								<input type="range" name="speed" min="0.5" max="2.0" step="0.1" value="1.0">
								<div class="hint">Left: Slower | Right: Faster</div>
							</div>
						</div>

						<div class="control-row">
							<div>
								<label>Voice Sharpness (Noise)</label>
								<input type="range" name="noise" min="0.1" max="1.5" step="0.1" value="0.6">
								<div class="hint">Low: Soft/Muffled | High: Crisp/Sharp</div>
							</div>
						</div>

						<button type="submit">🔊 Generate & Play Audio</button>
					</form>
				</div>
			</body>
			</html>
		`)
	})

	// Route 2: The Generation Logic
	http.HandleFunc("/speak", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Redirect(w, r, "/", http.StatusSeeOther)
			return
		}

		r.ParseForm()
		speedVal, _ := strconv.ParseFloat(r.FormValue("speed"), 32)
		noiseVal, _ := strconv.ParseFloat(r.FormValue("noise"), 32)

		ctx, cancel := context.WithTimeout(context.Background(), time.Minute*3)
		defer cancel()

		// Calling Python with the new Protobuf fields
		resp, err := client.Speak(ctx, &pb.SpeakRequest{
			Text:  r.FormValue("text"),
			Voice: r.FormValue("voice"),
			Speed: float32(speedVal),
			Noise: float32(noiseVal),
		})

		if err != nil || !resp.Success {
			http.Error(w, "AI Engine Error: Check if piper models are downloaded.", 500)
			return
		}

		// Success Page: Includes the Unix timestamp (?t=...) to force browser to ignore old cache
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, `
			<html>
			<body style="text-align:center; padding-top:100px; font-family:sans-serif; background:#f0f2f5;">
				<div style="background:white; display:inline-block; padding:40px; border-radius:12px; shadow:0 2px 10px rgba(0,0,0,0.1);">
					<h2>✅ Audio Generated</h2>
					<p>Playing with custom speed and sharpness...</p>
					<audio controls autoplay>
						<source src="/listen?t=%d" type="audio/wav">
					</audio>
					<br><br>
					<a href="/" style="text-decoration:none; color:#1877f2; font-weight:bold;">← Back to Editor</a>
				</div>
			</body>
			</html>
		`, time.Now().Unix())
	})

	// Route 3: Serving the static file from Python's folder
	http.HandleFunc("/listen", func(w http.ResponseWriter, r *http.Request) {
		// Prevent caching at the HTTP header level too
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Pragma", "no-cache")
		w.Header().Set("Expires", "0")
		w.Header().Set("Content-Type", "audio/wav")
		http.ServeFile(w, r, "../engine-python/output.wav")
	})

	fmt.Println("🌐 EchoSonic Gateway running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
