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
)

select
    m.* exclude (salary_mid, weekly_hours),
    case m.salary_per
        when 'Hour' then m.salary_mid * coalesce(m.weekly_hours, 40) * 52
        when 'Day' then m.salary_mid * 260
        when 'Week' then m.salary_mid * 52
        when 'Bi-weekly' then m.salary_mid * 26
        when 'Month' then m.salary_mid * 12
        when 'Year' then m.salary_mid
    end as annual_salary,
    o.family as occupation_family,
    o.family is not null as is_tech,
    coalesce(m.economic_region = 'Toronto Region', false) as is_toronto
from midpoints as m
left join occupations as o on o.noc_code = m.noc_code;
