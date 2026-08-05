select
  id,
  steps,
  runner_id,
  conclusion,
  status,
  run_attempt,
  run_url,
  head_sha,
  head_branch
from
  github_actions_repository_workflow_job
where
  repository_full_name = 'turbot/steampipe'
  and run_id = 26404053809
  and conclusion = 'failure';