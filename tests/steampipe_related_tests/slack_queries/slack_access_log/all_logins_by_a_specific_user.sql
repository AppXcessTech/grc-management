select
  user_name,
  ip,
  user_agent,
  date_first
from
  slack_access_log
where
  user_name = 'jim.halpert'
order by
  date_first;