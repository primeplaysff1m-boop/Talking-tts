# Voxreel

Script to narrated video preview — free, no signup. Type a script, pick a real voice, get synced captions over an animated background, or export plain narration audio.

## How it works

Voxreel is a single static page (`index.html`) — no build step, no server of its own. It calls your existing **Vocalis** TTS backend (already deployed on Vercel) directly from the browser for real Microsoft Edge Neural voices.

Because the voice backend is already live on the internet, voices show up automatically the moment you open `index.html` — nothing needs to be run locally.

## Adding to your existing GitHub repo

Drop this folder in alongside your Vocalis project, e.g.:

```
your-repo/
├── backend/          (existing Vocalis backend)
├── frontend/          (existing Vocalis frontend)
└── voxreel/            <- add this folder
    ├── index.html
    └── README.md
```

Then deploy `voxreel/` as its own Vercel project (Root Directory: `voxreel`) or any static host (GitHub Pages, Netlify) — it needs no environment variables or backend of its own.

## Optional: AI scene detection

Toggle "AI scene detection" in the video tab and paste a tokenrouter.com API key to have Qwen3.8-Max split your script into scenes with visual keywords, which switch the background template automatically as the narration plays. The key is only kept in memory for that browser tab and is never stored or sent anywhere except tokenrouter.com.

## Roadmap

- Real stock-footage backgrounds (free via Pexels API) instead of color templates
- Downloadable final video export (via ffmpeg.wasm, fully client-side, no paid rendering server)

## License

MIT
