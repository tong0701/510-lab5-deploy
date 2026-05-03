# Component E: GIX events browser

## Architecture map

```
[User browser]
   |  HTTP request / HTML response (Streamlit server-rendered UI)
   v
[Streamlit Python server (app.py)]
   |  JSON over HTTPS via supabase-py (PostgREST)
   v
[Supabase Postgres (public.events)]
```

### Boundaries

**1. Browser to Streamlit**

- **Data format crossing:** HTML and WebSocket or long-poll for interactive widgets. User actions become Python reruns with widget state.
- **One potential error:** Network loss or timeout while the app reruns, so the page stalls or shows a generic Streamlit error boundary.

**2. Streamlit to Supabase**

- **Data format crossing:** Python dicts and lists mapped to JSON rows for `events` and `checkouts`. Filters such as category lists become PostgREST query parameters.
- **One potential error:** Invalid or expired API key, project paused, or PostgREST error, which surfaces as an exception from the client and is caught in `app.py`.

**3. Supabase to Postgres**

- **Data format crossing:** SQL executed against typed tables (`events`, `checkouts`). Rows return as JSON-compatible objects.
- **One potential error:** Missing table, RLS denying reads, or malformed rows (nulls in required columns), which can yield empty data, errors, or rows skipped in the UI.

## Three error scenario tests

### 1. Database connection failure

- **What I did:** Stopped Supabase project or removed `SUPABASE_URL` / `SUPABASE_KEY` from Streamlit Secrets (or local `.env`), then opened the **GIX events** tab and triggered a load.
- **Expected:** Red error text: `Cannot reach the events database. Try refreshing.` No event cards render.
- **Actual:** (Fill after you run this check.) The tab shows that error and returns before cards when the client is missing or the category query raises.

### 2. Empty filter result (all categories deselected)

- **What I did:** Opened **GIX events**, cleared every chip in the category multiselect so the selection list is empty.
- **Expected:** Blue info banner: `Select at least one category to see events.` No query for filtered rows runs for that state.
- **Actual:** (Fill after you run this check.) You should see that info message and no cards until at least one category is selected again.

### 3. Malformed event row (missing title, event_date, or category)

- **What I did:** Inserted a test row in `events` with `title` null or empty while other fields were set, or used an existing bad seed row if present, then reloaded the tab.
- **Expected:** That row is skipped, valid rows still render, and if any rows were skipped the app shows `N events were hidden due to missing data.` with `st.warning`.
- **Actual:** (Fill after you run this check.) Count and warning should match the number of skipped rows.

## Security

- Supabase URL and key are read from `os.environ` after `load_dotenv`, with the same `st.secrets` fallback as Component B. No new secret names were added.
- `.env` stays in `.gitignore` and must not be committed.
- No API keys or database passwords appear in source files.
- This matches the Component B setup: one Supabase project, same credentials for checkouts and events.
