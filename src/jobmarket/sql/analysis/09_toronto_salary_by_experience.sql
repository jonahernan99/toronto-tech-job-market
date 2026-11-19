-- Title: Salary by experience asked for, Toronto Region tech postings (CAD)
-- Only direct employer postings report experience, so this table covers them
-- alone; their salaries are lower than those of external postings. Plausible
-- salaries, one row per posting, percentiles rounded to the nearest $100.
with toronto as (
    select *
    from postings
    where is_tech and is_toronto and experience is not null and salary_is_plausible
    qualify row_number() over (partition by posting_key order by posting_id) = 1
)
select
    experience_level as experience,
    count(*) as postings,
    round(quantile_cont(annual_salary, 0.25), -2) as p25,
    round(median(annual_salary), -2) as median,
    round(quantile_cont(annual_salary, 0.75), -2) as p75
from toronto
group by experience_level, experience_rank
order by experience_rank, experience;
