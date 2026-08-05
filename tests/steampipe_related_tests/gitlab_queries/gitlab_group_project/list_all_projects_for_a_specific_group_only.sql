select
  id,
  name,
  full_path,
  description,
  default_branch,
  public,
  visibility,
  archived.
  web_url
from
  gitlab_group_project
where
  group_id = 1234
and
  namespace_id = 1234;