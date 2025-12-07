Site Analytic — small prototype

Quick start (Windows PowerShell):

1) Open project folder:

```powershell
cd "C:\Users\anryinc\Desktop\Site analitic"
```

2) Create venv and activate:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3) Install dependencies:

```powershell
pip install -r requirements.txt
```

4) Copy `.env.example` to `.env` and fill values:

- `SUPABASE_REST_URL` — your Supabase base URL (e.g. `https://<project>.supabase.co`)
- `SUPABASE_SERVICE_KEY` — service key (keep secret)
- `SUPABASE_REST_TABLE` — table name (e.g. `Analytics`)

5) Run the app:

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

6) Open in browser:

- UI: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/api/analytics`

Security note:
- Do not commit `.env` to git. Add `.env` to `.gitignore` (already done).
- Use the service key only from server-side code. If you plan to host this app publicly, rotate keys and use server-side secrets management.

Next steps:
- Adjust field names in `static/index.html` mapping (`created_at`, `value`) to your schema.
- Add pagination/caching if your data is large.
- When ready, I can help create a `Dockerfile`, CI workflow and a `.github` push guide.
