select
  name,
  your_permission,
  can_administer,
  can_create_projects,
  can_subscribe,
  can_update_topics,
  possible_commit_emails
from
  github_repository
where
  full_name = 'turbot/steampipe';