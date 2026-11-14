# Data Foundry — dbt + DuckDB

**Autora: Marymar Danytza Calloticona Chambilla**

An executable batch data engineering solution: deterministic CSV ingestion, typed staging, dimensional validation, latest-event deduplication, quarantine, silver facts, gold aggregates, automated quality tests and public documentation/output delivery. No AWS account or service is configured or required.

## Public application

The GitHub Actions pipeline builds a static data product and dbt documentation for GitHub Pages. This is a published snapshot, not a continuously running database/API. See `delivery/links.json` for verified publication links and pending video status.

## Architecture

```text
Synthetic CSV events + customer/product dimensions
    → dbt seed (bronze)
    → stg_order_events (parse, validate, rank)
    → fct_orders (silver) + quarantine (audit)
    → daily_sales + market_sales (gold)
    → dbt tests + independent Python revenue reconciliation
    → JSON/CSV + dbt docs → GitHub Pages
```

The sample has 1,006 events: 1,000 accepted unique orders, five invalid events, and one superseded event. Every raw event is accounted for by a fact or quarantine row. Amounts use decimal arithmetic and a common USD unit; no currency conversion is performed.

## Run

Python 3.12 is used in CI.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-lock.txt
python scripts/generate_data.py
dbt build --profiles-dir .
python scripts/export_site.py
dbt docs generate --profiles-dir .
python scripts/package_docs.py
python -m http.server 8000 --directory site
```

Open http://localhost:8000. dbt uses the local `profiles.yml`; it contains no credentials. The database is created at `warehouse/retail.duckdb`. Scripts assume the repository root is the current working directory. Local telemetry can be disabled with `DBT_SEND_ANONYMOUS_USAGE_STATS=false`, as in CI.

`requirements.txt` records the top-level package versions; `requirements-lock.txt` records the tested Python environment. `seeds/` contains generated, public, entirely synthetic data. Re-running the generator reproduces these inputs.

## Quality policy

- Parse dates, integer quantities and decimal prices with `try_cast`.
- Validate customer and product references.
- Latest `event_id` wins for an order. If the latest event is invalid, quarantine it; do not silently restore an older order version.
- Preserve invalid and superseded events with explicit `disposition` values.
- Test unique/not-null keys, relationships, positive measures and conservation of events/revenue.
- Independently compute expected revenue from CSV with Python Decimal/integer cents before exporting.

dbt `ref()` declares dependencies and exposes model lineage in the generated documentation. `dbt build` runs seeds, models and tests according to the dependency graph. A failing build prevents publication.

## Automation

Create a public repository and set **Settings → Pages → Source → GitHub Actions**. On push to `main` or manual workflow dispatch, `.github/workflows/pipeline.yml` executes the pipeline, validates outputs, generates docs, saves evidence and deploys `site/` to Pages with a short-lived workflow token. No external cloud API secret is needed. Only static outputs are deployed; the DuckDB file is excluded from the website.

## Limits

This is an educational batch workflow with synthetic inputs. It does not demonstrate CDC, distributed ingestion, incremental loading or streaming. The warehouse lives on the CI runner and is rebuilt per run; Pages serves its exported results. The example uses tiny reference dimensions as seeds; production ingestion would use external sources and access controls. Public artifacts must contain only publishable data.

## Materials

- `docs/article-devto.md`: article source.
- `docs/video-script.md`: recording guide, 4:30 maximum planned duration.
- `evidence/pipeline-validation.json`: actual local execution evidence.
- `delivery/`: verified public links; video and Telegram remain Marymar's responsibility by her instruction.

## References

- [dbt build](https://docs.getdbt.com/reference/commands/build)
- [dbt seed](https://docs.getdbt.com/reference/commands/seed)
- [dbt data tests](https://docs.getdbt.com/reference/commands/test)
- [dbt-duckdb](https://github.com/duckdb/dbt-duckdb)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

MIT license. The synthetic dataset is dedicated to the public domain under CC0.
