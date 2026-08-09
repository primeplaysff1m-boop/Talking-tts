# Vocalis

A simple free text-to-speech website using Edge TTS.

## Features

- No sign-in
- No sign-up
- No Supabase
- No account system
- Language and voice selection
- Live character counter
- Adjustable speed (-50% to +100%)
- Adjustable pitch (-50Hz to +50Hz)
- Custom audio player
- MP3 download
- Responsive desktop/mobile UI

## Project Structure

```text
vocalis-tts/
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── index.html
```

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

Open `frontend/index.html` directly in a browser, or serve the folder with a static file server.

Set the `API_BASE` value near the top of the script in `frontend/index.html` to your backend URL.

## API

| Method | Endpoint | Body | Description |
|---|---|---|---|
| GET | `/` | — | Health check |
| GET | `/voices?lang=en-US` | — | List voices |
| GET | `/languages` | — | List available locales |
| POST | `/speak` | `{ text, voice, rate, pitch }` | Generate MP3 |

Example:

```bash
curl -X POST https://your-backend.example/speak   -H "Content-Type: application/json"   -d '{"text":"Hello world","voice":"en-US-AnaNeural","rate":"+0%","pitch":"+0Hz"}'   --output speech.mp3
```

## Important

This project does not include authentication, user accounts, Supabase, subscriptions, or sign-in/sign-up flows.

For a public deployment, add appropriate server-side rate limiting and abuse protection before allowing unrestricted traffic.
