select
  organization,
  state,
  dependency_package_ecosystem,
  dependency_package_name
from
  github_organization_dependabot_alert
where
  organization = 'my_org'
  and state = 'open';