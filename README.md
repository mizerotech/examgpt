# 🤖 Cluely Server — The AI Brain

> “The robot teacher that never sleeps.” — Powering Cluely.exe, Rwanda’s most viral exam cheat engine.

## 💡 What It Does

- Receives screenshots of exam questions from `Cluely.exe` (student’s PC).
- Uses **Google Gemini 1.5 Flash** to solve ANY question (Math, Code, History, Physics).
- Returns **ONLY the final answer** — clean, fast, undetectable.
- Deployed on **Render.com** — free, scalable, always-on.

## 🚀 How It Works

```mermaid
graph LR
A[Cluely.exe] -->|POST screenshot.jpg| B(Cluely Server on Render)
B --> C[Gemini AI]
C --> D[Returns Answer]
D --> A[Auto-types into exam]
