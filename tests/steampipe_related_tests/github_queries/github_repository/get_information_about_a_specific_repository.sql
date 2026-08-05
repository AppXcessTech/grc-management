select
  name,
  node_id,
  id,
  created_at,
  updated_at,
  disk_usage,
  owner_login,
  primary_language ->> 'name' as language,
  fork_count,
  stargazer_count,
  url,
  license_info ->> 'spdx_id' as license,
  description
from
  github_repository
where
  full_name = 'postgres/postgres';