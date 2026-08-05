select
  id,
  name,
  allow_force_push,
  code_owner_approval_required,
  push_access_levels,
  merge_access_levels,
  unprotect_access_levels
from
  gitlab_project_protected_branch
where
  project_id = 1258;