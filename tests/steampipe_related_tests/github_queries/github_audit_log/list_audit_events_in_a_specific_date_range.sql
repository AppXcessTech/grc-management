select
  id,
  created_at,
  actor,
  action,
  data
from
  github_audit_log
where
  organization = 'my_org'
  and created_at between '2022-06-27' and '2022-06-29'
order by
  created_at;