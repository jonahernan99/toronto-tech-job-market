-- Title: Repeated wide salary ranges in Toronto Region tech postings
-- A repeated wide range is a minimum and maximum that differ (for example
-- $30.00 to $69.74 an hour) and appear in at least 20 distinct Toronto tech
-- postings. In this data each one belongs to a single occupation, recurs across
-- months and comes from external job boards, so they look like occupation-wide
-- templates rather than individual offers. Round single values such as $50 an
-- hour also repeat, but across many occupations, and are not counted here.
-- Range midpoints drive the medians of external postings, which is why salaries
-- are also shown for direct employer postings alone (next table).
with toronto as (
    select *
    from postings
    where is_tech and is_toronto and salary_is_plausible
    qualify row_number() over (partition by posting_key order by posting_id) = 1
),
ranges as (
    select salary_per, salary_min, salary_max, count(*) as uses
    from toronto
    group by salary_per, salary_min, salary_max
),
labelled as (
    select
        case when is_external then 'External job boards' else 'Direct employer postings' end as source,
        uses >= 20 and salary_max > salary_min as is_repeated_range
    from toronto
    join ranges using (salary_per, salary_min, salary_max)
)
select
    coalesce(source, 'All') as source,
    count(*) as postings_with_salary,
    count(*) filter (where is_repeated_range) as in_repeated_ranges,
    round(100.0 * count(*) filter (where is_repeated_range) / count(*), 1) as repeated_pct
from labelled
group by grouping sets ((source), ())
order by grouping(source), source;
