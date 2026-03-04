**EchoSonic – Cloud-Deployed AI Text-to-Speech System**

EchoSonic is a production-ready AI Text-to-Speech (TTS) web application that converts text into natural-sounding speech using ONNX-based Piper voice models.

The system is optimized for performance and designed to run efficiently on free-tier cloud infrastructure while maintaining low latency and stable concurrent processing.


**Overview**

EchoSonic demonstrates practical AI model integration, backend optimization, and cloud deployment strategy.

It combines:

FastAPI backend for high-performance API handling

ONNX-based Piper voice models for speech synthesis

In-memory caching for performance acceleration

Thread-safe synthesis control

Static frontend hosted separately for lightweight scalability

The project focuses on efficient AI inference under constrained compute environments.

**Architecture**

Frontend (GitHub Pages)
⬇
REST API (FastAPI Backend)
⬇
Piper ONNX Voice Model
⬇
WAV Audio Stream Response

The backend preloads all voice models at startup to eliminate repeated loading overhead and reduce request latency.

Key Features

Real-time text-to-speech generation

Multi-voice support

Model preloading during application startup

In-memory MD5-based audio caching

Thread-safe synthesis using global lock

Adjustable playback speed (frontend)

250-character input limit

Daily usage restriction for free-tier sustainability

Admin override mode for unrestricted testing

Fully cloud-deployed architecture
