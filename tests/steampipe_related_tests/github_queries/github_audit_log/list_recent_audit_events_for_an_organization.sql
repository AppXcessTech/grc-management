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
order by
  created_at
limit 10;