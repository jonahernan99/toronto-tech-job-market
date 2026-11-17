-- Title: Education asked for in Toronto Region tech postings
-- Only direct employer postings report education, so external postings are
-- left out of the percentages. Levels are ordered from lowest to highest.
with toronto as (
    select *
    from postings
    where is_tech and is_toronto and education is not null
    qualify row_number() over (partition by posting_key order by posting_id) = 1
)
select
    education_level as education,
    count(*) as postings,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
from toronto
group by education_level, education_rank
order by education_rank, education;
