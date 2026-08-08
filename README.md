# Vocalis

Free, unlimited text-to-speech web app with natural-sounding voices in multiple languages and accents.

## Project Structure

```
vocalis-tts/
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── index.html
```

## Features

- Language and voice selection
- Live character counter
- Adjustable speed (-50% to +100%) and pitch (-50Hz to +50Hz)
- Custom audio player with play/pause, progress bar, and download
- Fully responsive (desktop + mobile)
- No signup, no usage limits

## Local Development

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

Open `frontend/index.html` directly in a browser, or serve it with any static file server. Make sure `API_BASE` near the top of the `<script>` tag points to your backend URL.

## Deployment (Vercel)

This project deploys as **two separate Vercel projects** from the same GitHub repo:

1. **Backend** — New Project → select this repo → Root Directory: `backend` → Deploy.
   Vercel auto-detects the FastAPI app in `main.py`. No extra config file is needed.
2. **Frontend** — New Project → select this repo again → Root Directory: `frontend` → Deploy.
   Before deploying, set `API_BASE` in `frontend/index.html` to your backend's live URL.

## API Reference

| Method | Endpoint | Body | Description |
|---|---|---|---|
| GET | `/` | — | Health check |
| GET | `/voices?lang=en-US` | — | List voices (optionally filtered by locale) |
| GET | `/languages` | — | List all available locales |
| POST | `/speak` | `{ text, voice, rate, pitch }` | Returns generated MP3 audio |

Example:
```bash
curl -X POST https://your-backend.vercel.app/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "en-US-AnaNeural", "rate": "+0%", "pitch": "+0Hz"}' \
  --output speech.mp3
```

## License

MIT
