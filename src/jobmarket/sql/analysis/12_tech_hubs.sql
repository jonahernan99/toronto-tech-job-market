-- Title: Toronto compared with Canada's other tech hubs (CAD)
-- The eight economic regions with the most distinct tech postings, chosen by
-- that rule rather than by hand. A posting listed in two regions counts once
-- in each. Salaries are shown for all postings and for direct employer
-- postings alone, because external job boards' repeated template ranges raise
-- the all-postings median. Direct samples outside Toronto are small, so read
-- the counts. Plausible salaries, medians rounded to the nearest $100.
with one_per_region as (
    select *
    from postings
    where is_tech and economic_region is not null
    qualify row_number() over (partition by posting_key, economic_region order by posting_id) = 1
)
select
    economic_region as region,
    min(province) as province,
    count(*) as postings,
    round(100.0 * count(*) filter (where not is_external) / count(*), 1) as direct_pct,
    round(median(annual_salary) filter (where salary_is_plausible), -2) as median_all,
    count(*) filter (where salary_is_plausible and not is_external) as direct_salaries,
    round(median(annual_salary) filter (where salary_is_plausible and not is_external), -2)
        as median_direct
from one_per_region
group by economic_region
order by postings desc, region
limit 8;
