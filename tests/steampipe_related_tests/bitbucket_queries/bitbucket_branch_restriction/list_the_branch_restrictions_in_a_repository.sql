select
  repository_full_name,
  id,
  self_link,
  kind,
  value,
  type
from
  bitbucket_branch_restriction
where
  repository_full_name = 'sayan97tb/stmp-rep';