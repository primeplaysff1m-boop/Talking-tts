-- Run this in Supabase Dashboard → SQL Editor → New Query → Run

create table if not exists profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  plan text default 'free',       -- 'free' or 'pro'
  free_used boolean default false,
  created_at timestamp with time zone default now()
);

alter table profiles enable row level security;

create policy "Users can view own profile"
  on profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on profiles for update
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on profiles for insert
  with check (auth.uid() = id);

-- To manually upgrade someone to Pro after they pay via WhatsApp,
-- run this (replace the email):
--
-- update profiles set plan = 'pro' where email = 'someone@example.com';
