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
  phrase = 'action:protected_branch.policy_override created:2022-06-28'
order by
  created_at;