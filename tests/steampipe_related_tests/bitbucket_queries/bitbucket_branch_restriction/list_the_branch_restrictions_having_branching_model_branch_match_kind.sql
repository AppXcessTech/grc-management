select
  repository_full_name,
  id,
  self_link,
  pattern,
  branch_match_kind
from
  bitbucket_branch_restriction
where
  repository_full_name = 'sayan97tb/stmp-rep'
  and branch_match_kind = 'branching_model';