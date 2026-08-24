-- Document Summary Assistant — run in the Supabase SQL editor.
-- Requires: Authentication > Email enabled (OTP).

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  original_filename text not null,
  content_type text not null,
  file_size_bytes integer not null check (file_size_bytes > 0),
  storage_path text,
  extraction_method text check (extraction_method in ('pymupdf', 'ocr', 'hybrid')),
  extracted_text text,
  page_count integer,
  status text not null default 'processing'
    check (status in ('processing', 'ready', 'failed')),
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.summaries (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  mode text not null check (mode in ('short', 'medium', 'long')),
  summary_text text not null,
  key_points jsonb not null default '[]'::jsonb,
  model text not null,
  created_at timestamptz not null default now(),
  unique (document_id, mode)
);

create index if not exists documents_user_created_idx
  on public.documents (user_id, created_at desc);

create index if not exists summaries_document_idx
  on public.summaries (document_id);

create index if not exists summaries_user_idx
  on public.summaries (user_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists documents_set_updated_at on public.documents;
create trigger documents_set_updated_at
  before update on public.documents
  for each row
  execute procedure public.set_updated_at();

alter table public.documents enable row level security;
alter table public.summaries enable row level security;

drop policy if exists "documents_select_own" on public.documents;
drop policy if exists "documents_insert_own" on public.documents;
drop policy if exists "documents_update_own" on public.documents;
drop policy if exists "documents_delete_own" on public.documents;

create policy "documents_select_own" on public.documents
  for select using (user_id = auth.uid());
create policy "documents_insert_own" on public.documents
  for insert with check (user_id = auth.uid());
create policy "documents_update_own" on public.documents
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "documents_delete_own" on public.documents
  for delete using (user_id = auth.uid());

drop policy if exists "summaries_select_own" on public.summaries;
drop policy if exists "summaries_insert_own" on public.summaries;
drop policy if exists "summaries_update_own" on public.summaries;
drop policy if exists "summaries_delete_own" on public.summaries;

create policy "summaries_select_own" on public.summaries
  for select using (user_id = auth.uid());
create policy "summaries_insert_own" on public.summaries
  for insert with check (user_id = auth.uid());
create policy "summaries_update_own" on public.summaries
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "summaries_delete_own" on public.summaries
  for delete using (user_id = auth.uid());

grant select, insert, update, delete on public.documents to authenticated;
grant select, insert, update, delete on public.summaries to authenticated;

-- Storage Bucket for Original Document Binaries (Private)
insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;

drop policy if exists "documents_storage_select_own" on storage.objects;
drop policy if exists "documents_storage_insert_own" on storage.objects;
drop policy if exists "documents_storage_update_own" on storage.objects;
drop policy if exists "documents_storage_delete_own" on storage.objects;

create policy "documents_storage_select_own" on storage.objects
  for select using (bucket_id = 'documents' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "documents_storage_insert_own" on storage.objects
  for insert with check (bucket_id = 'documents' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "documents_storage_update_own" on storage.objects
  for update using (bucket_id = 'documents' and auth.uid()::text = (storage.foldername(name))[1])
  with check (bucket_id = 'documents' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "documents_storage_delete_own" on storage.objects
  for delete using (bucket_id = 'documents' and auth.uid()::text = (storage.foldername(name))[1]);

