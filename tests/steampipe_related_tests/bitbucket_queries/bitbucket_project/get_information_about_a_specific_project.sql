select
  name,
  uuid,
  key as project_key,
  workspace_slug,
  owner_display_name,
  is_private
from
  bitbucket_project
where
  workspace_slug = 'np1981';