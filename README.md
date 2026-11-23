# Toronto Tech Job Market

[![CI](https://github.com/jonahernan99/toronto-tech-job-market/actions/workflows/ci.yml/badge.svg)](https://github.com/jonahernan99/toronto-tech-job-market/actions/workflows/ci.yml)
[![Dashboard](https://img.shields.io/badge/dashboard-live-2a78d6)](https://jonahernan99.github.io/toronto-tech-job-market/)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![SQL](https://img.shields.io/badge/SQL-DuckDB-FFF000)
![License](https://img.shields.io/badge/license-MIT-green)

**What does the tech job market in Toronto look like in official government data?**
A reproducible SQL analysis of a year of postings from Canada's National Job
Bank: which tech occupations are hiring, what they pay, and how demand changes
month to month.

> **Try it:** the [interactive dashboard](https://jonahernan99.github.io/toronto-tech-job-market/)
> compares Toronto with the rest of Canada or with another tech hub, such as
> Vancouver, Montréal or Ottawa, by occupation family, source and period.
>
> **Not technical?** Start with
> [`notebooks/findings.ipynb`](notebooks/findings.ipynb): five questions a job
> seeker would ask, answered in plain words with charts.

## Interactive dashboard

[![Dashboard: tiles with Toronto and rest-of-Canada postings and median salaries, a monthly trend chart and salaries by family](docs/dashboard.png)](https://jonahernan99.github.io/toronto-tech-job-market/)

The [dashboard](https://jonahernan99.github.io/toronto-tech-job-market/) is a
static page on GitHub Pages with no server. `jobmarket export` writes one row
per tech posting and economic region (11,756 rows for 11,025 postings, no
employer names) to
[`dashboard/data/tech_postings.csv`](dashboard/data/tech_postings.csv), and the
page computes every count and median from that file in the browser, with the
same rules as the SQL report. Its numbers were checked against
[`reports/summary.md`](reports/summary.md); for example, direct software
postings give $95,000 in Toronto and $90,000 elsewhere in both.

- Filter by period, occupation family and source (direct employer postings or
  external job boards). Filters are kept in the URL, so a view can be shared as
  a link, for example
  [data jobs, direct postings only](https://jonahernan99.github.io/toronto-tech-job-market/?family=Data&source=Direct+employer).
- Compare Toronto with the rest of Canada or with one of the seven next largest
  tech regions, for example
  [Vancouver, direct postings only](https://jonahernan99.github.io/toronto-tech-job-market/?source=Direct+employer&compare=Lower+Mainland%E2%80%93Southwest+Region).
  For the rest of Canada, an ad listed in several regions counts once.
- Choosing a family breaks salaries down by occupation.
- Every chart has hover and keyboard tooltips and a table view, and the page
  follows the system's light or dark mode.
- The extract is [documented](dashboard/data/README.md) and can be downloaded
  for use in a spreadsheet or BI tool.

## First findings

From the 12 monthly files for November 2025 to October 2026 (601,330 rows,
11,025 distinct tech postings, 5,074 of them in the Toronto Region). The full
tables are in [`reports/summary.md`](reports/summary.md).

1. **Toronto holds about half of Canada's tech postings on Job Bank:** 51% of
   software postings and 55% of data postings are in the Toronto Region.
2. **Advertised salaries are higher in Toronto, but by less than the headline
   numbers suggest.** Across all postings, the median is higher in every tech
   family:

   ![Median salary by tech family, Toronto Region vs. rest of Canada](reports/figures/salary_by_family.png)

   | Family | Toronto | Rest of Canada |
   | --- | ---: | ---: |
   | Software | $117,500 | $92,500 |
   | Security | $104,300 | $100,700 |
   | Data | $103,700 | $89,500 |
   | IT & systems | $93,300 | $81,000 |
   | Web | $83,100 | $72,800 |
   | Networks & support | $74,900 | $69,200 |

   Many of these salaries come from external job boards that reuse one wide
   range per occupation (finding 6). Counting only postings that employers
   publish on Job Bank themselves, Toronto still pays more in five of six
   families, but the gaps shrink: software $95,000 vs. $90,000, data $90,000
   vs. $80,000, and web pays *less* in Toronto ($65,500 vs. $68,300). The
   direct postings are fewer (29 to 252 per family in Toronto), so these
   figures are noisier.

3. **The most advertised Toronto roles** are information systems specialists
   (1,381 postings), software developers (909), software engineers (621) and
   data scientists (421).
4. **Toronto's share dropped in the second half of the period,** from about
   50% between December and April to 38–43% between June and October. One
   year of data cannot tell a seasonal pattern from a trend.

   ![Monthly tech postings, Toronto Region vs. Canada](reports/figures/monthly_trend.png)
5. **Most postings ask for a degree and some experience.** Of the Toronto tech
   postings that state requirements, half ask for a bachelor's degree and
   48% ask for 1 to 3 years of experience.
6. **A quarter of salaries are templates, not offers.** 21 wide ranges, such
   as $30.00 to $69.74 an hour for data scientists or $35.00 to $91.35 for
   software engineers, each used for a single occupation, cover 27% of Toronto
   tech postings with a salary. All of them come from external job boards and
   repeat across months and job titles; none appears in a direct employer
   posting. A range that wide says little about what one job pays, and its
   midpoint is what enters the median.
7. **Pay rises with the experience asked for.** In direct employer postings,
   the median goes from about $61,000 to $71,000 for roles asking up to 2
   years, to $93,600 for 3 to 5 years and $109,200 for 5 years or more.

   ![Salary by experience asked for in Toronto Region tech postings](reports/figures/salary_by_experience.png)
8. **Toronto has four times the tech postings of any other region, but not the
   highest direct pay.** Vancouver (1,250 postings) and Montréal (892) follow
   Toronto's 5,074. Across all postings Toronto's median is the highest
   ($99,600), but in direct employer postings Ottawa is above it ($84,200 from
   78 salaries vs. $80,000), and Vancouver, Kitchener–Waterloo, Calgary,
   Montréal and Edmonton are within $3,300 to $7,000. Halifax shows how much
   external boards can move a median: $94,300 across all postings, $65,800 in
   its 34 direct ones. Salaries are not adjusted for the cost of living.

   ![Median salaries in the eight largest tech regions, all postings vs. direct employer postings](reports/figures/tech_hubs.png)

These figures describe Job Bank, not the whole market (see
[Limitations](#limitations)). Salary ranges for some occupations are narrow,
which may reflect employers who must advertise on Job Bank, for example when
applying to hire through federal programs.

## How the numbers are counted

- **Rows vs. distinct postings.** Job Bank lists one row per work location, so
  14% of rows repeat an ad in another city. Analyses count distinct postings,
  matched by title, occupation, date, salary and terms. The data has no
  employer name, so identical ads from different employers would merge too.
- **Plausible salaries only.** Some postings enter an hourly rate as a yearly
  salary or the reverse. Salaries whose implied hourly rate falls outside $12
  to $250 are excluded from salary statistics (0.4% of hourly and 1.3% of
  yearly salaries).
- **Medians, not averages,** with each posting counted once per region.
- **Direct vs. external postings.** 83% of Toronto tech postings come from
  external job boards, which do not report education or experience and often
  reuse occupation-wide salary ranges. Salaries are shown for all postings and
  for direct employer postings alone, so the effect of those ranges is visible.

Tech means one of [15 NOC 2021 occupations](src/jobmarket/occupations.py),
from software developers and data scientists to user support technicians.

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
pip install -e ".[charts]"
jobmarket download --last 12      # about 0.5 GB of CSV files
jobmarket build                   # creates data/jobmarket.duckdb
jobmarket report                  # SQL analysis + charts in reports/ (needs the charts extra)
jobmarket export                  # dashboard/data/tech_postings.csv for the dashboard
```

To preview the dashboard locally, serve the folder (browsers block `fetch` on
`file://` pages) and open http://localhost:8000:

```bash
python -m http.server 8000 --directory dashboard
```

The plain-language notebook reads the same database. Install the `notebook`
extra and point it at the database if it is not in `data/`:

```bash
pip install -e ".[notebook]"
JOBMARKET_DB=data/jobmarket.duckdb jupyter nbconvert --to notebook --execute --inplace notebooks/findings.ipynb
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
  The same goes for "Various Location", which is "No" everywhere.
- **Overlapping education labels:** "College/CEGEP" appears alongside longer
  labels for college programs of 3 months to 1 year and of 1 to 2 years, in
  every month. The source does not define how "College/CEGEP" differs from
  them, so the three are kept apart.
- **Requirements are partial:** education and experience are only reported by
  direct employer postings, about a third of all rows.
- **Template salary ranges:** about a third of external tech postings in
  Toronto reuse one wide range per occupation. They are kept, since they are
  real advertised ranges, but measured in a separate table and compared with
  direct postings. Why the boards use them cannot be determined from the data.
- **Salary outliers exist** (for example, hourly rates entered as yearly). They
  are flagged with a documented rule and excluded from salary statistics, but a
  wrong salary inside the $12 to $250 hourly range cannot be detected.

## Roadmap

- [x] Download monthly files from the official API
- [x] DuckDB pipeline with a cleaned, typed `postings` view
- [x] Salary outlier rules and posting de-duplication across locations
- [x] SQL analysis: demand by occupation, salaries, education and experience, trends
- [x] `jobmarket report`: Markdown report generated from the SQL queries
- [x] Ordered education and experience levels with short labels
- [x] Charts in the generated report (salaries, monthly trend, education)
- [x] Check for repeated template salary ranges; salaries by experience and for direct postings
- [x] Notebook with written findings for a non-technical reader
- [x] Interactive dashboard on GitHub Pages, fed by a documented CSV extract
- [x] Comparison with Canada's other tech hubs

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
data files are not stored in the repository; the dashboard extract in
`dashboard/data/` is derived from them under the same licence.
