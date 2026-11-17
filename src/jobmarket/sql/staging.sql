-- Clean, typed view over the raw Job Bank rows.
--
-- One row is one posting at one work location in one monthly snapshot.
-- Job Bank writes missing values as 'NA'; columns missing from older monthly
-- files arrive as NULL. Salaries are converted to an annual figure:
--   Hour      x weekly hours x 52 (weekly hours from the posting, else 40)
--   Day       x 260 (5 days x 52 weeks)
--   Week      x 52
--   Bi-weekly x 26
--   Month     x 12
-- A posting's salary is the midpoint of its minimum and maximum.
--
-- Salary plausibility: some postings enter an hourly rate as a yearly salary
-- (742 "yearly" salaries under $1,000) or a yearly salary as an hourly rate
-- (hourly rates up to $200,000). A salary is plausible when its implied hourly
-- rate is between $12 (below every provincial minimum wage) and $250 (about
-- $520,000 a year). Implausible salaries stay visible but are excluded from
-- salary statistics.
--
-- posting_key: Job Bank lists one row per work location, so the same posting
-- can appear once per city. Rows sharing title, occupation, first posting date,
-- salary, employment terms and month get the same key. The data has no
-- employer name, so different employers posting identical ads would also share
-- a key: report both row counts and distinct keys.

create or replace view postings as
with typed as (
    select
        "WIC Job Location Snapshot ID" as posting_id,
        strptime(regexp_extract(source_file, '(\d{4}-\d{2})\.csv$', 1), '%Y-%m')::date
            as source_month,
        nullif(trim("Job Title"), '') as job_title,
        nullif("NOC21 Code", 'NA') as noc_code,
        nullif("NOC21 Code Name", 'NA') as noc_name,
        "External Indicator" = '1' as is_external,
        try_strptime(nullif("First Posting Date", 'NA'), '%Y/%m/%d')::date as first_posting_date,
        try_cast(nullif("Vacancy Count", 'NA') as integer) as vacancies,
        nullif("Education LOS", 'NA') as education,
        nullif("Experience Level", 'NA') as experience,
        nullif("NAICS", 'NA') as industry,
        nullif("Province/Territory", 'NA') as province,
        nullif("City", 'NA') as city,
        nullif("Economic Region", 'NA') as economic_region,
        nullif("Employment Type", 'NA') as employment_type,
        nullif("Employment Term", 'NA') as employment_term,
        nullif("Salary Per", 'NA') as salary_per,
        try_cast(nullif("Salary Minimum", 'NA') as double) as salary_min,
        try_cast(nullif("Salary Maximum", 'NA') as double) as salary_max,
        nullif("Hours Per", 'NA') as hours_per,
        try_cast(nullif("Hours Minimum", 'NA') as double) as hours_min,
        try_cast(nullif("Hours Maximum", 'NA') as double) as hours_max
    from raw_postings
),

midpoints as (
    select
        *,
        (salary_min + coalesce(salary_max, salary_min)) / 2 as salary_mid,
        case
            when hours_per = 'Week'
                and (hours_min + coalesce(hours_max, hours_min)) / 2 between 1 and 80
                then (hours_min + coalesce(hours_max, hours_min)) / 2
        end as weekly_hours
    from typed
),

annualized as (
    select
        m.*,
        case m.salary_per
            when 'Hour' then m.salary_mid * coalesce(m.weekly_hours, 40) * 52
            when 'Day' then m.salary_mid * 260
            when 'Week' then m.salary_mid * 52
            when 'Bi-weekly' then m.salary_mid * 26
            when 'Month' then m.salary_mid * 12
            when 'Year' then m.salary_mid
        end as annual_salary
    from midpoints as m
)

select
    a.* exclude (salary_mid, weekly_hours),
    a.annual_salary / (coalesce(a.weekly_hours, 40) * 52) as implied_hourly,
    case
        when a.annual_salary is not null
            then a.annual_salary / (coalesce(a.weekly_hours, 40) * 52) between 12 and 250
    end as salary_is_plausible,
    md5(concat_ws('|',
        lower(coalesce(a.job_title, '')), coalesce(a.noc_code, ''),
        coalesce(cast(a.first_posting_date as varchar), ''), coalesce(a.salary_per, ''),
        coalesce(cast(a.salary_min as varchar), ''), coalesce(cast(a.salary_max as varchar), ''),
        coalesce(a.employment_type, ''), coalesce(a.employment_term, ''),
        cast(a.source_month as varchar)
    )) as posting_key,
    o.family as occupation_family,
    o.family is not null as is_tech,
    coalesce(a.economic_region = 'Toronto Region', false) as is_toronto,
    case when a.education is not null then coalesce(ed.short_label, a.education) end
        as education_level,
    case when a.education is not null then coalesce(ed.rank, 99) end as education_rank,
    case when a.experience is not null then coalesce(ex.short_label, a.experience) end
        as experience_level,
    case when a.experience is not null then coalesce(ex.rank, 99) end as experience_rank
from annualized as a
left join occupations as o on o.noc_code = a.noc_code
left join education_levels as ed on ed.label = a.education
left join experience_levels as ex on ex.label = a.experience;
