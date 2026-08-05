select
  id,
  name,
  full_path,
  description,
  visibility,
  parent_id,
  created_at
from
  gitlab_group_subgroup
where
  parent_id = 34234;