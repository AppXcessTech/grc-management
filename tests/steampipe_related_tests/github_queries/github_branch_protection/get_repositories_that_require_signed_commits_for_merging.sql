select 
  repository_full_name,
  pattern,
  matching_branches
from 
  github_branch_protection
where
  repository_full_name = 'turbot/steampipe'
and
  requires_commit_signatures = true;