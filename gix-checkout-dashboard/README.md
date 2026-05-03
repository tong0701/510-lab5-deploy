# GIX Checkout Dashboard

**GitHub (grading / source of truth):** [https://github.com/GIX-Luyao/lab-5-tong0701](https://github.com/GIX-Luyao/lab-5-tong0701) — branch `main`.

**Streamlit Cloud:** New app → repo `GIX-Luyao/lab-5-tong0701` → main file path is either `app.py` (repo root) or `gix-checkout-dashboard/app.py` (if this project is in that subfolder). Add Secrets: `SUPABASE_URL`, `SUPABASE_KEY` (TOML format in the Cloud UI).

---

This Streamlit app gives GIX students a self-serve, phone-friendly view of equipment they have checked out and when each item is due. It reads live rows from Supabase, adds a short Seattle weather heads-up from Open-Meteo when heavy rain is in the three-day forecast, and separates active loans from returned history so staff spend less time on reactive overdue email.

## Setup

1. Clone the repository and enter the project folder (if the app lives in a subfolder, `cd` into that folder next).
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate` (on Windows use `.venv\Scripts\activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set `SUPABASE_URL` and `SUPABASE_KEY` from your Supabase project settings (Project URL and anon or service role key your policy allows for reads).
6. In Supabase, create the `checkouts` table and seed data (see below), and turn off RLS for that table if you use the anon key for demos.
7. Run the app: `streamlit run app.py`

## Deploy on Streamlit Cloud

1. Push to GitHub ([GIX-Luyao/lab-5-tong0701](https://github.com/GIX-Luyao/lab-5-tong0701)). Confirm `.env` is **not** in the repo (see `.gitignore`); use `.env.example` only in git.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Click **New app**, select repository **GIX-Luyao/lab-5-tong0701**, branch **main**, then set **Main file path** to where `app.py` lives in that repo:
   - If `app.py` is at the repository root: enter `app.py`.
   - If the dashboard is under a subfolder (for example `gix-checkout-dashboard/`): enter `gix-checkout-dashboard/app.py`.
4. In the app **Settings**, open **Secrets** and add TOML entries (see Streamlit secrets docs for the exact editor format), for example:

   ```
   SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
   SUPABASE_KEY = "your-anon-or-service-key"
   ```

   The app reads these through `os.environ` after `load_dotenv()` for local `.env` files, and falls back to `st.secrets` so the same names work on Streamlit Cloud.

5. Redeploy after changing secrets.

## Supabase schema and sample seed

Run the schema in the Supabase SQL Editor:

```sql
create table checkouts (
  id uuid primary key default gen_random_uuid(),
  student_email text not null,
  item_name text not null,
  item_category text not null,
  checkout_date timestamptz not null default now(),
  due_date timestamptz not null,
  returned boolean not null default false,
  notes text,
  created_at timestamptz not null default now()
);

create index checkouts_student_email_idx on checkouts(student_email);
create index checkouts_due_date_idx on checkouts(due_date);
```

Then disable RLS on `checkouts` in the Table Editor if you need open reads for the demo.

Example seed rows (adjust timestamps relative to when you run the script):

```sql
insert into checkouts (student_email, item_name, item_category, checkout_date, due_date, returned, notes) values
  ('ada@uw.edu', 'Sony A7 kit', 'camera', now() - interval '3 days', now() + interval '4 days', false, 'Include both batteries'),
  ('ada@uw.edu', 'USB-C hub', 'cable', now() - interval '1 day', now() + interval '6 days', false, null),
  ('ada@uw.edu', 'Shure SM7B', 'microphone', now() - interval '10 days', now() - interval '2 days', false, 'Pop filter attached'),
  ('ben@uw.edu', 'MacBook Pro 16', 'laptop', now() - interval '20 days', now() - interval '1 day', false, 'Asset tag GIX-4421'),
  ('ben@uw.edu', 'HDMI 2m', 'cable', now() - interval '30 days', now() - interval '5 days', true, null),
  ('chen@gixnetwork.org', 'Sony WH-1000XM5', 'headset', now() - interval '14 days', now() - interval '7 days', true, 'Returned with case'),
  ('chen@gixnetwork.org', 'Rode Wireless GO II', 'microphone', now() - interval '5 days', now() + interval '2 days', false, null);
```

## Contract tests

`pytest.ini` sets `pythonpath = .` so tests can import `data` and `app` helpers.

These tests call the real Open-Meteo API (no key) and the real Supabase `events` table for Component E (needs `.env` with valid credentials). From the project root with the venv active:

```bash
pytest tests/
```

Verbose output:

```bash
pytest tests/ -v
```
