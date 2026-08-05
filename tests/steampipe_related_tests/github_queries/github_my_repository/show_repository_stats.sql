select
  name,
  owner_login,
  primary_language ->> 'name' as language,
  fork_count,
  stargazer_count,
  subscribers_count,
  watchers_total_count,
  updated_at as last_updated,
  description
from
  github_my_repository;