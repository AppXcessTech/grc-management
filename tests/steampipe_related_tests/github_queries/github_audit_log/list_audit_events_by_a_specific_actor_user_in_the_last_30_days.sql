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
  and actor = 'some_user'
  and created_at > now() - interval '30 day'
order by
  created_at;