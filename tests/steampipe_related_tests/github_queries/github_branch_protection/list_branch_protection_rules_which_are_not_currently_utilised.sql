select
  *
from
  github_branch_protection
where
  repository_full_name = 'turbot/steampipe'
and 
  matching_branches = 0;