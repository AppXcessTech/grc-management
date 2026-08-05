select
  login as organization,
  members_with_role_total_count as members_count,
  members_allowed_repository_creation_type,
  members_can_create_internal_repos,
  members_can_create_pages,
  members_can_create_private_repos,
  members_can_create_public_repos,
  members_can_create_repos,
  default_repo_permission,
  two_factor_requirement_enabled
from
  github_my_organization;