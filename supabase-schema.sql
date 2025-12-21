begin;

-- 1) Drop table cũ
drop table if exists public.dataset cascade;

-- 2) Drop enum types cũ (nếu có)
drop type if exists public.objects_present cascade;
drop type if exists public.auto_flags cascade;
drop type if exists public.error_tags cascade;
drop type if exists public.page_type cascade;
drop type if exists public.review_priority cascade;
drop type if exists public.is_checked cascade;

-- 3) Create enum types (controlled vocabulary)

-- objects_present (ALLOWED OBJECT LABELS)
create type public.objects_present as enum (
  'person_child','person_adult','student','teacher',
  'animal_generic','animal_pet','animal_farm','animal_wild',
  'food_fruit','food_vegetable','food_bundle',
  'book','notebook','pen','pencil','school_bag',
  'clock_analog','clock_digital','countable_object','grouped_object',
  'table','chart','illustration_scene'
);

-- page_type
create type public.page_type as enum (
  'cover','title_page','toc','content','exercise','blank','other'
);

-- review_priority
create type public.review_priority as enum ('low','normal','high');

-- auto_flags
create type public.auto_flags as enum (
  'OCR_UNREADABLE','OCR_LONG','HAS_TABLE','LAYOUT_COMPLEX',
  'POSSIBLE_BLANK','LOW_CERTAINTY','COUNTING_WRONG','CLOCK_READING_WRONG'
);

-- error_tags (taxonomy)
create type public.error_tags as enum (
  'OCR_MISSING','OCR_WRONG','OCR_UNREADABLE','OCR_NOT_CONTEXTUALIZED',
  'HALLUCINATION','WRONG_LAYOUT','SUBJECTIVE_REASONING','TOO_LONG_SHORT',
  'DETAIL_INCOHERENT_FLOW','MISQUOTED_TEXT',
  'COUNTING_WRONG','CLOCK_READING_WRONG',
  'ID_ISSUE','IMAGE_MISMATCH'
);

-- is_checked  
create type public.is_checked as enum (
  'unchecked', 'checked', 'reviewed'
);

-- 4) Create table dataset (enum + enum[])
create table public.dataset (
  id              text primary key,
  image           text,

  page_type       public.page_type not null default 'other',
  has_text        boolean,
  has_table       boolean,

  objects_present public.objects_present[] not null default '{}'::public.objects_present[],

  caption_short   text,
  caption_detail  text,
  text_in_image   text,

  review_priority public.review_priority not null default 'normal',

  auto_flags      public.auto_flags[] not null default '{}'::public.auto_flags[],

  notes           text,
  is_checked      public.is_checked not null default 'unchecked',

  error_tags      public.error_tags[] not null default '{}'::public.error_tags[],

  change_log      text,

  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- 5) Trigger auto-update updated_at
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_dataset_set_updated_at on public.dataset;

create trigger trg_dataset_set_updated_at
before update on public.dataset
for each row
execute function public.set_updated_at();

-- 6) Indexes (tuỳ nhu cầu)
create index if not exists idx_dataset_is_checked on public.dataset (is_checked);
create index if not exists idx_dataset_review_priority on public.dataset (review_priority);

-- 7) Grants (nếu dùng client-side)
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on table public.dataset to anon, authenticated;

commit;
