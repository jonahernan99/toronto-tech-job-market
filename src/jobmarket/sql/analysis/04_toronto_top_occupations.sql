-- Title: Top tech occupations in the Toronto Region
-- Distinct postings, with the salary range of those that state a plausible
-- salary (25th, 50th and 75th percentiles, CAD, rounded to $100).
with toronto as (
    select *
    from postings
    where is_tech and is_toronto
    qualify row_number() over (partition by posting_key order by posting_id) = 1
)
select
    noc_name as occupation,
    count(*) as postings,
    count(*) filter (where salary_is_plausible) as with_salary,
    round(quantile_cont(annual_salary, 0.25) filter (where salary_is_plausible), -2) as p25,
    round(median(annual_salary) filter (where salary_is_plausible), -2) as median,
    round(quantile_cont(annual_salary, 0.75) filter (where salary_is_plausible), -2) as p75
from toronto
group by noc_name
order by postings desc, occupation
limit 10;
