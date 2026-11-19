-- Title: Median annual salary by family, direct employer postings only (CAD)
-- The same comparison as the salary table above, restricted to postings that
-- employers publish on Job Bank themselves, where repeated template ranges are
-- rare. Samples are smaller, so read differences of a few thousand dollars with
-- care. Plausible salaries, one row per posting and region, rounded to $100.
with one_per_posting as (
    select *
    from postings
    where is_tech and salary_is_plausible and not is_external
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
