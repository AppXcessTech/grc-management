select
  id,
  event,
  workflow_id,
  conclusion,
  status,
  run_number,
  workflow_url,
  head_commit,
  head_branch
from
    github_actions_repository_workflow_run
where
  repository_full_name = 'turbot/steampipe'
  and conclusion = 'failure';