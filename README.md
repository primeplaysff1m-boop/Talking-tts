# VoxReel + credit system

This package upgrades your existing Vocalis backend and adds VoxReel
(script-to-narrated-video) with a **free daily credit system per device**
— no login required.

- Voice-only generation: **1 credit**
- Video generation: **5 credits** (heavier — narration + scene analysis)
- Every device gets **30 free credits**, resetting at midnight (UTC)

If you skip the Supabase setup below, everything still works exactly as
before — credits just won't be enforced (unlimited, like today).

## 1. Replace files in your existing repo

```
your-repo/
├── backend/
│   ├── main.py              <- replace with the one in this package
│   ├── requirements.txt      <- replace (adds the supabase package)
│   └── credits_schema.sql    <- add this new file
└── voxreel/                  <- add this whole new folder
    └── index.html
```

Your existing `backend/Dockerfile`, `backend/vercel.json`, and the
original `frontend/` folder don't need to change.

## 2. Create a free Supabase project (5 minutes)

1. Go to supabase.com → sign up free → "New project"
2. Once it's ready, open **SQL Editor** → paste the contents of
   `backend/credits_schema.sql` → Run
3. Go to **Project Settings → API** and copy:
   - `Project URL`
   - `service_role` secret key (NOT the `anon` key — this one must stay
     secret, so it only ever goes in your backend's environment variables,
     never in frontend code)

## 3. Add environment variables in Vercel

On your backend's Vercel project → **Settings → Environment Variables**:

| Name | Value |
|---|---|
| `SUPABASE_URL` | the Project URL from step 2 |
| `SUPABASE_SERVICE_KEY` | the service_role secret key from step 2 |

Redeploy the backend after adding these.

## 4. Deploy VoxReel

Deploy the `voxreel/` folder as its own static site (new Vercel project
with Root Directory: `voxreel`, or GitHub Pages, or Netlify — no build
step needed). It already points at your live backend
(`https://talking-tts-38rr.vercel.app`).

## How it works

- The browser generates a random device id on first visit and stores it
  in `localStorage` — no account needed.
- Every request to `/speak` sends that id in an `X-Device-Id` header.
- The backend checks/deducts credits in Supabase before generating audio,
  and returns the remaining balance in an `X-Credits-Remaining` header.
- VoxReel shows the live balance next to the server status, and disables
  the Generate button once credits hit 0 for the day.

## Adjusting the numbers

In `backend/main.py`:

```python
DAILY_FREE_CREDITS = 30
COST_AUDIO = 1
COST_VIDEO = 5
```

Change these and redeploy the backend any time.
