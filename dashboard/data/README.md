# Tech postings extract

`tech_postings.csv` holds one row per tech job posting and economic region
from the Job Bank files of November 2025 to October 2026: 11,756 rows for
11,025 distinct postings. It feeds the dashboard and can be opened in any
spreadsheet or BI tool. Regenerate it after
`jobmarket build` with:

```bash
jobmarket export --db data/jobmarket.duckdb
```

## Columns

| Column | Meaning |
| --- | --- |
| `posting` | Identifier of the posting, shared by its rows in different regions |
| `month` | Monthly file the posting comes from (`YYYY-MM`) |
| `region` | `Toronto Region` (Job Bank's economic region) or `Rest of Canada` |
| `economic_region` | Job Bank's economic region, such as `Ottawa Region`; empty for 274 rows without one |
| `family` | Occupation family used in the analysis (Data, Software, Web, Security, IT & systems, Networks & support) |
| `noc_code`, `occupation` | NOC 2021 code and its official name |
| `source` | `Direct employer` (published on Job Bank by the employer) or `External job board` |
| `experience`, `experience_rank` | Experience asked for, short label and order (0 = none); direct postings only |
| `education`, `education_rank` | Education asked for, short label and order (0 = no formal education); direct postings only |
| `annual_salary` | Annual salary in CAD, rounded to the dollar, as defined in [`staging.sql`](../../src/jobmarket/sql/staging.sql); empty when missing or implausible |

## Counting rules

- An ad listed in several cities of the same economic region is one row, as
  in the analysis queries. An ad listed in Ottawa and in Calgary is one row for
  each region, with the same `posting`. **To count postings for a group of
  regions, such as the rest of Canada, count distinct `posting` values**:
  5,074 in the Toronto Region and 6,243 elsewhere. Rows of one posting share
  its month and occupation; for a handful of the 432 postings listed in
  several regions, the source, requirements or weekly hours (and so the annual
  salary) differ between regions.
- Salaries follow the plausibility rule in `staging.sql` (implied hourly rate
  between $12 and $250).
- Nine ads appear as both a direct and an external listing in the same region;
  each is kept once, as its first listing. A direct-only median can therefore
  differ by one posting from the table in
  [`reports/summary.md`](../../reports/summary.md), which keeps both.
- No employer names or job titles are included.

Contains information licensed under the
[Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).
Source: [Job Postings Advertised on Canada's National Job Bank Website](https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072),
Employment and Social Development Canada.
