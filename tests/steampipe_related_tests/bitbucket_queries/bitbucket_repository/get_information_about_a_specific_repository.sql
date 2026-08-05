select
  name,
  uuid,
  full_name,
  owner_display_name,
  description
from
  bitbucket_repository
where
  full_name = 'bitbucketpipelines/official-pipes'