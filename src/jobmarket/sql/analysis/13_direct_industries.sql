-- Title: Industries of direct employer tech postings (CAD)
-- Only employers posting on Job Bank themselves state their industry (NAICS
-- sector), so this table covers direct postings alone. Shares are of direct
-- tech postings with an industry in each region; the ten largest Toronto
-- industries are shown. Salaries are medians of plausible salaries, rounded to
-- $100. Large employers that recruit on their own sites, such as banks, are
-- largely absent from Job Bank, which this table makes visible.
with direct as (
    select *
    from postings
    where is_tech and not is_external and industry is not null
    qualify row_number() over (partition by posting_key, is_toronto order by posting_id) = 1
),
by_industry as (
    select
        industry,
        count(*) filter (where is_toronto) as toronto_postings,
        count(*) filter (where not is_toronto) as rest_postings,
        round(median(annual_salary) filter (where is_toronto and salary_is_plausible), -2)
            as toronto_median
    from direct
    group by industry
)
select
    industry,
    toronto_postings,
    round(100.0 * toronto_postings / sum(toronto_postings) over (), 1) as toronto_pct,
    toronto_median,
    rest_postings,
    round(100.0 * rest_postings / sum(rest_postings) over (), 1) as rest_pct
from by_industry
order by toronto_postings desc, industry
limit 10;
