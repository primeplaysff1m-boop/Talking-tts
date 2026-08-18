-- Run this in Supabase Dashboard -> SQL Editor -> New Query -> Run
-- Adds anonymous, device-based daily credits. No login required.

create table if not exists device_credits (
  device_id text primary key,
  credits integer not null default 30,
  last_reset date not null default current_date
);

-- Backend talks to this table using the service role key only (never expose
-- that key to the browser), so row level security can stay locked down.
alter table device_credits enable row level security;

-- No policies are added on purpose: only the service role (used by the
-- backend server) can read/write. Browser clients get zero direct access.

-- Optional: to manually top up a device's credits (e.g. after a request),
-- run this (replace the id):
--
-- update device_credits set credits = 100 where device_id = 'paste-device-id-here';
