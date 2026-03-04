# 🎙️ EchoSonic AI
**Professional-grade AI Text-to-Speech powered by Piper ONNX.**

EchoSonic is a production-ready TTS engine optimized for high-performance synthesis on constrained cloud infrastructure. By leveraging ONNX-based models and a FastAPI backbone, it delivers low-latency, natural-sounding speech without the high costs of proprietary APIs.

---

## 🚀 Key Features
* **High-Fidelity Synthesis:** Uses Piper ONNX models for near-human vocal quality.
* **Performance Optimized:** In-memory MD5-based audio caching and model preloading.
* **Multi-Voice Support:** Toggle between different personas (e.g., Amy, Ryan).
* **Smart Rate Limiting:** Built-in character constraints with an **Admin MFA Override** for power users.
* **Cloud-Native:** Designed specifically for Google Cloud Run (Backend) and GitHub Pages (Frontend).

---

## 🏗️ System Architecture

EchoSonic utilizes a decoupled architecture to ensure maximum uptime and zero-cost frontend hosting.



1.  **UI (GitHub Pages):** A modern, glassmorphic React-style interface.
2.  **API Gateway (Cloud Run):** FastAPI handles request validation and JWT-based authentication.
3.  **Inference Engine:** Piper TTS processes text-to-audio in a thread-safe environment.
4.  **Audio Stream:** 16-bit Mono WAV data is streamed directly back to the client for instant playback.

---

## 🛠️ Technical Stack
| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI Engine** | Piper TTS (ONNX Runtime) |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| **Security** | PyOTP (MFA), JWT (JSON Web Tokens) |
| **Deployment** | Docker, Google Cloud Run, GitHub Pages |

---

## 💻 Local Development

### 1. Clone & Setup
```bash
git clone [https://github.com/YOUR_USERNAME/EchoSonic.git](https://github.com/YOUR_USERNAME/EchoSonic.git)
cd EchoSonic
pip install -r requirements.txt