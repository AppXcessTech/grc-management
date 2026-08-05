select
  state,
  dependency_package_ecosystem,
  dependency_package_name
from
  github_repository_dependabot_alert
where
  repository_full_name = 'turbot/steampipe'
  and state = 'open';