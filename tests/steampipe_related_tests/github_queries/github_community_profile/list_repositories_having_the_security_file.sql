select
  repository_full_name,
  security ->> 'text' as security_file_content
from
  github_community_profile c
  join github_my_repository r on r.name_with_owner = c.repository_full_name
  where security is not null;