select
  repository_full_name,
  bitbucket_branch_restriction.id,
  self_link,
  pattern,
  u ->> 'display_name' as user_name
from
  bitbucket_branch_restriction,
  jsonb_array_elements(users) as u
where
  repository_full_name = 'sayan97tb/stmp-rep'
  and u ->> 'display_name' = 'sayan';