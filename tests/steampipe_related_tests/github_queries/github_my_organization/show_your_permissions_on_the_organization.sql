select
  login as organization,
  members_with_role_total_count as members_count,
  can_administer,
  can_changed_pinned_items,
  can_create_projects,
  can_create_repositories,
  can_create_teams,
  is_a_member as current_member
from
  github_my_organization;