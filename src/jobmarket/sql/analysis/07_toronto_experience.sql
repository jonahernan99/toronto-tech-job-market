-- Title: Experience asked for in Toronto Region tech postings
-- Only direct employer postings report experience, so external postings are
-- left out of the percentages.
with toronto as (
    select *
    from postings
    where is_tech and is_toronto and experience is not null
    qualify row_number() over (partition by posting_key order by posting_id) = 1
)
select
    experience,
    count(*) as postings,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
from toronto
group by experience
order by postings desc, experience;
