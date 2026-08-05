select
  *
from
  github_actions_repository_workflow_job
where
  repository_full_name = 'turbot/steampipe'
  and run_id = 26404053809;