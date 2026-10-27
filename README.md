# AI Data Analyst — Natural Language to SQL (GenAI)

Ask business questions in plain Hindi/English — get instant answers + charts from your own shop data.
Built with Flask + OpenAI (GPT-4o mini), with a rule-based fallback so the app never goes down.

## ✨ What it does

Type a question like:
- `Total revenue kitna hai?`
- `Top 5 products by sales`
- `Last 30 days me kitne orders aaye?`

The app converts your question → SQL → results + a chart. No SQL knowledge needed.

## 🏗️ How it works

1. **Schema-aware prompting** — the live database schema is injected into the prompt so the LLM
   generates valid SQLite against real table/column names (`products`, `customers`, `orders`).
2. **Guardrails** — only `SELECT` statements are allowed; the LLM can never run destructive queries.
3. **Graceful degradation** — if the OpenAI API is unavailable (no key / network / rate limit),
   a rule-based converter (`rule_based_sql.py`) answers common question patterns locally.
4. **Charts** — results are rendered as bar/line/pie charts via matplotlib (Agg backend).

```
templates/   Flask UI (login, PIN, dashboard)
static/      CSS + JS
app.py       routes, sessions, uploads (CSV/XLSX, 5MB limit), chart generation
database.py  SQLite schema (products / customers / orders), CRUD helpers
text_to_sql.py       OpenAI → SQL with schema-aware prompt
rule_based_sql.py    offline fallback NL → SQL
data/       sample SQLite databases
```

## 🚀 Run it

```bash
pip install -r requirements.txt
set OPENAI_API_KEY=sk-...   # optional — app falls back to rule-based mode without it
python app.py
```

## 🔐 Security notes

- Only `SELECT` queries are ever executed (read-only analytics).
- API key is read from the environment, never hard-coded.
- Shop sessions are PIN + login protected.
