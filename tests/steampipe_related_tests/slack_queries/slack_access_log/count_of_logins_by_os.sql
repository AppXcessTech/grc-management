with count_by_os as (
  select
    user_agent,
    count,
    case
      when user_agent ilike '%android%' then 'Android'
      when user_agent ilike '%ios%' then 'iOS'
      when user_agent ilike '%macintosh%' then 'MacOS'
      when user_agent ilike '%windows%' then 'Windows'
      else 'Other'
    end as os
  from
    slack_access_log
)
select
  os,
  sum(count)
from
  count_by_os
group by
  os
order by
  sum desc;