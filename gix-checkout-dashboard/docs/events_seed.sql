-- Seed or refresh events from Supabase table export (events_rows.csv).
-- Run in Supabase SQL Editor. Requires public.events with uuid primary key on id.

insert into events (id, title, category, event_date, location, description, created_at)
values
  (
    '01b1ab71-08ec-47f3-917b-91e33a96c88b'::uuid,
    'End of quarter showcase',
    'showcase',
    '2026-05-31 00:58:08.171953+00'::timestamptz,
    'GIX Atrium',
    'Demo your final projects to faculty and industry',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    '106c564b-0a0f-4aa3-8309-44f89365ab76'::uuid,
    'Embedded systems guest lecture',
    'guest lecture',
    '2026-05-23 00:58:08.171953+00'::timestamptz,
    'Room 234',
    'From Microsoft Azure IoT team',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    '23441dff-8943-4c37-8d71-4b61292af422'::uuid,
    'Figma design jam',
    'workshop',
    '2026-05-15 00:58:08.171953+00'::timestamptz,
    'Room 301',
    'Bring laptops, food provided',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    '3590e579-378c-4997-84cb-eda617cbdf1d'::uuid,
    'Industry panel: Climate tech',
    'career',
    '2026-05-13 00:58:08.171953+00'::timestamptz,
    'GIX Auditorium',
    'Five founders share what they look for in hires',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    '585bd01f-d259-4be2-af32-76e370c0aa12'::uuid,
    'Hardware hackathon kickoff',
    'workshop',
    '2026-05-10 00:58:08.171953+00'::timestamptz,
    'Maker Space',
    'Teams of 3-4, prizes for top 3',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    '7352da39-cb1c-4f8f-a020-643b70f5ff1c'::uuid,
    'Alumni networking night',
    'career',
    '2026-05-17 00:58:08.171953+00'::timestamptz,
    'GIX Lounge',
    'Light dinner included',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    'be707e1f-51bc-424e-9aab-7d187f18f9de'::uuid,
    'Resume workshop',
    'career',
    '2026-05-08 00:58:08.171953+00'::timestamptz,
    'Room 234',
    'Bring printed copies for peer review',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  ),
  (
    'f1a9d24d-b9b6-462e-9d6d-9e7a8fa61832'::uuid,
    'AI in Healthcare guest lecture',
    'guest lecture',
    '2026-05-06 00:58:08.171953+00'::timestamptz,
    'GIX Auditorium',
    'Dr. Chen from UW Medicine on AI diagnostics',
    '2026-05-03 00:58:08.171953+00'::timestamptz
  )
on conflict (id) do update set
  title = excluded.title,
  category = excluded.category,
  event_date = excluded.event_date,
  location = excluded.location,
  description = excluded.description,
  created_at = excluded.created_at;
