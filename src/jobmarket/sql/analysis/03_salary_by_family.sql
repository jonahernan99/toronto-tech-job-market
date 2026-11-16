-- Title: Median annual salary by family, Toronto Region vs. rest of Canada (CAD)
-- Plausible salaries only, one row per posting and region so an ad repeated
-- in many cities is not weighted several times. Rounded to the nearest $100.
with one_per_posting as (
    select *
    from postings
    where is_tech and salary_is_plausible
    qualify row_number() over (partition by posting_key, is_toronto order by posting_id) = 1
)
select
    occupation_family as family,
    count(*) filter (where is_toronto) as toronto_postings,
    round(median(annual_salary) filter (where is_toronto), -2) as toronto_median,
    count(*) filter (where not is_toronto) as rest_postings,
    round(median(annual_salary) filter (where not is_toronto), -2) as rest_of_canada_median
from one_per_posting
group by occupation_family
order by toronto_postings desc, family;
