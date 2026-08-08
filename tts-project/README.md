# Vocalis

Free, unlimited text-to-speech web app with natural-sounding voices in multiple languages and accents.

## Live

- Website: https://vocalis-tts.vercel.app

## Project Structure

```
vocalis-tts/
├── backend/       API server
├── frontend/      Website
└── README.md
```

## Features

- Unlimited text-to-speech generation
- Multiple languages and voices (male & female)
- Adjustable speech speed
- Instant MP3 playback and download
- No signup, no usage limits

## Local Development

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

Open `frontend/index.html` in your browser, or serve it with any static file server.

## Deployment

Both `backend/` and `frontend/` are deployed as separate projects on Vercel, using the repository's `backend` and `frontend` folders as their respective root directories.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/voices` | List available voices |
| GET | `/languages` | List available languages |
| POST | `/speak` | Generate speech from text |

## License

MIT
