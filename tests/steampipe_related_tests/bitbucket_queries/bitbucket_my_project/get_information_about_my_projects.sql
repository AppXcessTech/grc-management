select
  name,
  uuid,
  key as project_key,
  workspace_slug,
  owner_display_name,
  is_private,
  created
from
  bitbucket_my_project;