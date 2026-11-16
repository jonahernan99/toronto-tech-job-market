-- Title: Salary data quality by pay unit (all postings)
-- Rows whose implied hourly rate falls outside $12 to $250 are flagged as
-- implausible and excluded from salary statistics.
select
    coalesce(salary_per, 'missing') as pay_unit,
    count(*) as rows,
    count(*) filter (where salary_is_plausible = false) as implausible,
    round(100.0 * implausible / rows, 2) as implausible_pct
from postings
group by salary_per
order by rows desc;
