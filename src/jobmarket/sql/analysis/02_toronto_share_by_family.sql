-- Title: Share of Canada's tech postings located in the Toronto Region
-- Distinct postings per occupation family. An ad listed in Toronto and in
-- another region counts in both.
select
    occupation_family as family,
    count(distinct posting_key) as canada_postings,
    count(distinct posting_key) filter (where is_toronto) as toronto_postings,
    round(100.0 * toronto_postings / canada_postings, 1) as toronto_share_pct
from postings
where is_tech
group by occupation_family
order by canada_postings desc, family;
