select
  id,
  event,
  workflow_id,
  conclusion,
  status,
  run_number,
  workflow_url,
  head_commit,
  head_branch,
  actor_login,
  triggering_actor_login
from
  github_actions_repository_workflow_run
where
  repository_full_name = 'turbot/steampipe'
  and event = 'workflow_dispatch';