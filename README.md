# Vocalis — Script to Video upgrade

This replaces two files in your existing repo to add a **Script to Video**
tab directly into your live site (`talking-tts.vercel.app`), right next
to the existing Dashboard tab — same design, same site, one deployment.

Your original Text-to-Speech box is **untouched and still unlimited** —
credits only apply to the new Script to Video tab (video generation is
heavier, so it gets a free daily limit instead of being unlimited).

## What changed

- `frontend/index.html` — added a "Script to Video" nav link + a new
  section with script input, real-voice narration, synced captions,
  optional AI scene detection, and animated background templates.
- `backend/main.py` — added an optional daily credit system. It only
  activates for requests that send an `X-Device-Id` header (the new
  video tab does this). Your original TTS box doesn't send that header,
  so it keeps working exactly as before — unlimited.
- `backend/requirements.txt` — added the `supabase` package.
- `backend/credits_schema.sql` — new, run once in Supabase.

## 1. Replace files in your GitHub repo (browser, no coding needed)

In your repo:
- Open `frontend/index.html` → pencil (edit) icon → select all, delete,
  paste in the new version → Commit changes.
- Same for `backend/main.py` and `backend/requirements.txt`.
- Add `backend/credits_schema.sql` as a new file.

Vercel will redeploy automatically after each commit (both your existing
backend and frontend Vercel projects, since you're only editing files
already inside them — no new project needed this time).

## 2. Turn on credits (optional, 5 minutes)

Skip this and everything still works — the video tab just won't be
credit-limited yet (unlimited, like today).

1. supabase.com → sign up free → New project
2. SQL Editor → paste `backend/credits_schema.sql` → Run
3. Project Settings → API → copy the Project URL and the `service_role`
   secret key (never the `anon` key — this one is secret)
4. In Vercel, your **backend** project → Settings → Environment Variables:
   - `SUPABASE_URL` = the Project URL
   - `SUPABASE_SERVICE_KEY` = the service_role key
5. Redeploy the backend

## Adjusting the limits

In `backend/main.py`:

```python
DAILY_FREE_CREDITS = 30   # per device, per day
COST_AUDIO = 1             # not used by the main unlimited box
COST_VIDEO = 5             # per video generated in the new tab
```
