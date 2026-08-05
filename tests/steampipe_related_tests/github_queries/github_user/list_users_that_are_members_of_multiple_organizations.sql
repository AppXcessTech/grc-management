select
  name,
  email,
  created_at,
  bio,
  twitter_username,
  organizations_total_count
from
  github_user
where
  login = 'madhushreeray30'
  and organizations_total_count > 1;