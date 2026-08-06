select
  user_name,
  ip,
  sum(count)
from
  slack_access_log
where
  user_name = 'jim.halpert'
group by
  user_name,
  ip
order by
  sum desc;