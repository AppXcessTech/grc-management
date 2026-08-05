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
  and action IN ('repo.create', 'repo.destroy')
  and created_at = '2022-01-01'
order by
  created_at;