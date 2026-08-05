select
  login as organization,
  name,
  twitter_username,
  private_repositories_total_count as private_repos,
  public_repositories_total_count as public_repos,
  created_at,
  updated_at,
  is_verified,
  teams_total_count as teams_count,
  members_with_role_total_count as member_count,
  url
from
  github_my_organization;