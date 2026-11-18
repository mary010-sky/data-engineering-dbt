---
title: "Data Engineering with dbt and DuckDB: From Raw CSVs to a Public Data Product"
published: true
tags: dataengineering, dbt, python, devops
---

**Author: Marymar Danytza Calloticona Chambilla**

In this project, I built **Data Foundry**, a batch data engineering solution that turns sales events into reliable tables and publicly accessible results. I used dbt to organize transformations and tests, DuckDB as a local warehouse, and GitHub Actions to run the pipeline and deploy its outputs to GitHub Pages. I did not configure an AWS account or any AWS services.

My goal was to demonstrate more than a query against a CSV file: reproducible ingestion, explicit data quality rules, deduplication, traceability, testing, and automated delivery of a data product.

## 1. The problem: incoming data contains defects

The generator produces **1,006 synthetic events**, along with customer and product dimensions. The dataset contains 1,000 valid unique orders, a repeated version of one order, and five deliberately invalid events: an unparseable date, a negative quantity, an empty price, an unknown customer, and an unknown product.

These records do not represent real people or sales. Introducing known defects makes it possible to demonstrate how the pipeline handles them. Simply deleting problematic rows is insufficient: I want to know how many events arrived, how many were accepted, and why each retained event was set aside.

## 2. Architecture: bronze, silver, and gold

```text
Synthetic CSVs + dimensions
        ↓ dbt seed
BRONZE: raw_orders, customers, products
        ↓ type conversion + validation + version ranking
STAGING: stg_order_events
        ├── SILVER: fct_orders
        └── AUDIT: quarantine
                  ↓
GOLD: daily_sales, market_sales
        ↓ dbt tests + Python reconciliation
JSON / CSV / dbt documentation
        ↓ GitHub Actions
GitHub Pages: public data product
```

DuckDB runs while the pipeline is being built. The published website serves a snapshot of its outputs; it does not provide a shared database or run dbt in the browser.

## 3. Reproducible ingestion with seeds

The `scripts/generate_data.py` script generates the same input files on every run. `dbt seed` loads those CSV files as tables. Small dimensions work well as seeds in a lab; for production, I would use an ingestion process and source definitions appropriate to the actual data origin.

The [dbt seed documentation](https://docs.getdbt.com/reference/commands/seed) describes this loading mechanism. In this project, I explicitly type the original order fields as text so staging can identify conversion failures in a controlled way.

## 4. Transforming data without hiding errors

The `stg_order_events` model trims whitespace and uses `try_cast` to parse dates, quantities, and prices. An invalid conversion produces a null value, which the quality rules classify with an explicit reason.

```sql
select
  trim(order_id) as order_id,
  try_cast(order_date as date) as order_date,
  try_cast(quantity as integer) as quantity,
  try_cast(unit_price as decimal(12,2)) as unit_price
from {{ ref('raw_orders') }}
```

The model also checks keys against the dimensions. Records receive statuses such as `invalid_date`, `invalid_quantity`, `invalid_price`, `unknown_customer`, or `unknown_product`.

For multiple versions of an order, the policy is that the highest `event_id` wins:

```sql
row_number() over (
  partition by order_id
  order by event_id desc
) as event_rank
```

If the latest version is invalid, it is quarantined rather than silently falling back to an earlier version. Event identifiers are unique in this example; a real source would also require policies for ties and out-of-order events.

## 5. Preserving auditable outputs

`fct_orders` contains only the latest accepted version of each order. It calculates revenue with decimal arithmetic and adds the market and category from the dimensions.

`quarantine` preserves invalid events and earlier versions. A replaced version is labeled `superseded_event`, which distinguishes it from a data quality error. This allows the event counts to reconcile:

```text
1,006 events = 1,000 accepted orders + 6 retained events
6 retained events = 5 invalid events + 1 superseded version
```

The gold tables, `daily_sales` and `market_sales`, summarize orders, units, and revenue. USD is the common unit used for the example; no currency conversion is performed.

## 6. Testing is part of the build

dbt tests check unique and non-null keys, dimension relationships, allowed statuses, and valid measures. Additional SQL tests verify that no events disappear and that gold revenue totals reconcile with the silver table.

A singular dbt test returns the rows that violate its rule. If it returns a row, the test fails:

```sql
select 'unaccounted_events' as failure
where (select count(*) from {{ ref('raw_orders') }}) !=
      (select count(*) from {{ ref('fct_orders') }}) +
      (select count(*) from {{ ref('quarantine') }})
```

Python also rereads the CSV files, applies the documented policy, and independently calculates expected revenue in cents. It compares that result with DuckDB's decimal sum. This helps catch cases where two tables agree with each other because both share the same transformation error.

`scripts/export_site.py` exports outputs only when all tests recorded in `run_results.json` pass and the independent reconciliation agrees. The evidence is saved in `evidence/pipeline-validation.json`.

In the local execution, all **26 data tests** passed, along with all 34 resources processed by `dbt build`. The 1,000 accepted orders totaled **USD 154,075.00**, matching the independently calculated **15,407,500 cents**. The six retained events remained available for auditing. These amounts belong to the lab's synthetic dataset.

## 7. Lineage and documentation as pipeline outputs

Each `ref()` declares a dependency between models. dbt uses these references to build its graph and execute resources in the correct order. Afterward, `dbt docs generate` creates documentation for the tables, columns, and dependencies.

I publish that documentation alongside a small dashboard and CSV/JSON files. The dashboard lets readers inspect record counts, revenue by market, quarantine reasons, and daily results filtered by month. Its displayed values come from an actual pipeline execution rather than manually entered HTML metrics.

## 8. Automating execution and publication

The workflow starts on a push to `main` or a manual run. Its steps are:

1. Install the Python environment using recorded package versions.
2. Generate the input data.
3. Run `dbt build`, which loads seeds and processes models and tests according to the dependency graph.
4. Reconcile revenue and export the public outputs.
5. Generate and package the dbt documentation.
6. Save evidence artifacts and deploy the website to GitHub Pages.

The deployment job depends on the successful completion of the pipeline. A failed test prevents the new version from being published. GitHub Pages uses **GitHub Actions** as its source; the workflow relies on a short-lived token and does not need an API key for another cloud provider.

The repository includes the code and configuration needed to reproduce the process. The [dbt build reference](https://docs.getdbt.com/reference/commands/build) and [Pages workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) describe the mechanisms used.

## 9. Limitations and next steps

This solution demonstrates small-scale batch data engineering. It does not implement streaming, change data capture, incremental loading, or a persistent cloud warehouse. The DuckDB file is rebuilt on the CI runner, and the website serves its exported outputs.

To extend it, I would add an external source, business-specific quality rules, and a persistence strategy. I would retain the event conservation and revenue reconciliation checks to detect regressions.

**Author: Marymar Danytza Calloticona Chambilla.**

- [Public repository with models, tests, and automation](https://github.com/mary010-sky/data-engineering-dbt)
- [Public data product](https://mary010-sky.github.io/data-engineering-dbt/)
- [dbt documentation and lineage](https://mary010-sky.github.io/data-engineering-dbt/dbt/)
- [Successful automated execution](https://github.com/mary010-sky/data-engineering-dbt/actions/runs/43623819473)

The GitHub Actions execution completed successfully: both the pipeline and deployment passed. The public application showed all 26 tests passing, 1,000 accepted orders, and USD 154,075.00 in validated revenue. Its February filter returned 28 dates from the published snapshot.

This article and its code were prepared with AI assistance and execution checks.
