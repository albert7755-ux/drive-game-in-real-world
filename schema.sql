-- 債券賽車 共用排行榜
-- 到 Supabase「債速配」那個專案 → SQL Editor → New query → 整份貼上 → Run
-- 只會新增一張 race_scores 表，不會動到原本的 flip_scores、flight_scores

create table if not exists public.race_scores (
  id         bigserial primary key,
  board      text        not null check (char_length(board) between 1 and 80),
  name       text        not null check (char_length(name) between 1 and 12),
  score      integer     not null check (score between 0 and 20000),
  correct    smallint    not null check (correct between 0 and 20),
  seconds    real        not null check (seconds between 0 and 3600),
  crashes    smallint    not null default 0 check (crashes between 0 and 999),
  jumps      smallint    not null default 0 check (jumps between 0 and 50),
  created_at timestamptz not null default now()
);

create index if not exists race_scores_board_score_idx on public.race_scores (board, score desc);

alter table public.race_scores enable row level security;

drop policy if exists "race_scores 所有人可讀" on public.race_scores;
create policy "race_scores 所有人可讀" on public.race_scores for select to anon using (true);

drop policy if exists "race_scores 所有人可新增" on public.race_scores;
create policy "race_scores 所有人可新增" on public.race_scores for insert to anon with check (true);

grant select, insert on public.race_scores to anon;
grant usage, select on sequence public.race_scores_id_seq to anon;
