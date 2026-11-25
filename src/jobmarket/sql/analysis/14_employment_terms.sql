-- Title: Schedule and permanence of tech postings
-- Schedule (full or part time) is reported by both sources and covers all
-- postings; permanence (permanent, term or contract, ...) is reported only by
-- direct employer postings. Shares are within each region and measure. Most
-- part-time postings come from external job boards and give no weekly hours,
-- so their pay is annualized at 40 hours, a full-time equivalent.
with one_per_posting as (
    select *
    from postings
    where is_tech
    qualify row_number() over (partition by posting_key, is_toronto order by posting_id) = 1
),
labelled as (
    select is_toronto, 'Schedule' as measure, coalesce(employment_type, 'Not stated') as value
    from one_per_posting
    union all
    select is_toronto, 'Permanence (direct postings)', coalesce(employment_term, 'Not stated')
    from one_per_posting
    where not is_external
),
counted as (
    select
        measure,
        value,
        count(*) filter (where is_toronto) as toronto_postings,
        count(*) filter (where not is_toronto) as rest_postings
    from labelled
    group by measure, value
)
select
    measure,
    value,
    toronto_postings,
    round(100.0 * toronto_postings / sum(toronto_postings) over (partition by measure), 1)
        as toronto_pct,
    rest_postings,
    round(100.0 * rest_postings / sum(rest_postings) over (partition by measure), 1) as rest_pct
from counted
order by measure desc, toronto_postings desc, value;
