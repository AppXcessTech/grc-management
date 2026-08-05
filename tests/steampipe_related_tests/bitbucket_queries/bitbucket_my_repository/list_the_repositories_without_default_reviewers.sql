select
  name,
  uuid,
  full_name,
  owner_display_name
from
  bitbucket_my_repository
where
  default_reviewers is null;