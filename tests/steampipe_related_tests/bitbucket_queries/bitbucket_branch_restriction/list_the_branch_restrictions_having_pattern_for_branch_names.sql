select
  repository_full_name,
  id,
  self_link,
  pattern
from
  bitbucket_branch_restriction
where
  repository_full_name = 'sayan97tb/stmp-rep'
  and pattern = 'test-*';