-- Title: Overview
-- Rows are postings at one work location; distinct postings merge the same ad
-- repeated in several cities (see posting_key in staging.sql).
select
    count(distinct source_month) as months,
    count(*) as rows,
    count(distinct posting_key) as postings,
    count(*) filter (where is_tech) as tech_rows,
    count(distinct posting_key) filter (where is_tech) as tech_postings,
    count(*) filter (where is_tech and is_toronto) as toronto_tech_rows,
    count(distinct posting_key) filter (where is_tech and is_toronto) as toronto_tech_postings
from postings;
