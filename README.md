# Toronto Tech Job Market

[![CI](https://github.com/jonahernan99/toronto-tech-job-market/actions/workflows/ci.yml/badge.svg)](https://github.com/jonahernan99/toronto-tech-job-market/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![SQL](https://img.shields.io/badge/SQL-DuckDB-FFF000)
![License](https://img.shields.io/badge/license-MIT-green)

**What does the tech job market in Toronto look like in official government data?**
A reproducible SQL analysis of a year of postings from Canada's National Job
Bank: which tech occupations are hiring, what they pay, and how demand changes
month to month.

> **Status: work in progress.** The data pipeline is done and tested. The
> analysis, notebook and dashboard come next, so no conclusions are drawn yet.

## Data at a glance

From the 12 monthly files for November 2025 to October 2026:

| | |
| --- | --- |
| Rows loaded | 601,330 |
| Tech rows in Canada | 13,893 |
| Tech rows in the Toronto Region | 6,301 |
| Tech rows in the Toronto Region per month | 366 to 716 |

A row is one posting at one work location, so a job advertised in several
cities appears once per city. Tech means one of
[15 NOC 2021 occupations](src/jobmarket/occupations.py), from software
developers and data scientists to user support technicians.

## Pipeline

```text
open.canada.ca CKAN API ──> jobmarket download ──> data/raw/YYYY-MM.csv
                                                        │
                    jobmarket build (DuckDB) <──────────┘
                            │
                            ├── raw_postings   all columns, headers normalized
                            ├── occupations    tech occupation reference table
                            └── postings       typed, cleaned SQL view
```

```bash
pip install -e .
jobmarket download --last 12      # about 0.5 GB of CSV files
jobmarket build                   # creates data/jobmarket.duckdb
```

Then query it with any DuckDB client:

```sql
select occupation_family, count(*) as postings, median(annual_salary) as median_salary
from postings
where is_tech and is_toronto
group by occupation_family
order by postings desc;
```

## Data quality issues handled

Real government data is messy. The pipeline deals with:

- **Unusual encoding:** files are UTF-16, tab-separated text, not standard CSV.
- **Columns change over time:** "Official Language" exists in recent months
  only, so files are combined by column name, not position.
- **Inconsistent headers:** one column is spelled `Economic  Region`, with two
  spaces.
- **Irregular file names** (`oct2026`, `sept2026`, `july2026`): months are found
  through the CKAN API instead of guessing URLs.
- **Missing values** written as `NA`, converted to SQL `NULL`.
- **Salaries in six units** (hour, day, week, bi-weekly, month, year),
  converted to an annual figure. Hourly pay uses the posting's weekly hours, or
  40 hours when none are given. The rules are documented in
  [`staging.sql`](src/jobmarket/sql/staging.sql).
- **Occupation filters:** a code prefix such as `212` would also match
  architects and urban planners, so tech occupations are listed explicitly.

## Limitations

- **Job Bank is not the whole market.** Many tech employers post mainly on
  LinkedIn and their own career sites, so this data shows the market as seen
  on Job Bank and likely under-represents large tech companies.
- **No job descriptions.** The open data has titles and occupation codes but
  no description text, so skills cannot be extracted from it.
- **Telework is not usable:** the field is either "No" or missing in every row.
- **Salary outliers exist** (for example, hourly rates entered as yearly), and
  will be handled explicitly in the analysis before any figure is reported.

## Roadmap

- [x] Download monthly files from the official API
- [x] DuckDB pipeline with a cleaned, typed `postings` view
- [ ] Salary outlier rules and posting de-duplication across locations
- [ ] SQL analysis: demand by occupation, salaries, education and experience, trends
- [ ] Notebook with charts and written findings for a non-technical reader
- [ ] Interactive dashboard

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest --cov=jobmarket
```

Tests use small synthetic files in the real format, so they run without
downloading anything.

## Data source and license

Data: [Job Postings Advertised on Canada's National Job Bank Website](https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072),
Employment and Social Development Canada.

Contains information licensed under the
[Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).

The code in this repository is released under the [MIT License](LICENSE). Raw
data files are not stored in the repository.
