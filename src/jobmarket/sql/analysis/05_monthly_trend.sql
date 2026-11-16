-- Title: Monthly tech postings, Toronto Region vs. Canada
-- Distinct postings per monthly file.
select
    strftime(source_month, '%Y-%m') as month,
    count(distinct posting_key) filter (where is_toronto) as toronto_postings,
    count(distinct posting_key) as canada_postings,
    round(100.0 * toronto_postings / canada_postings, 1) as toronto_share_pct
from postings
where is_tech
group by source_month
order by source_month;
