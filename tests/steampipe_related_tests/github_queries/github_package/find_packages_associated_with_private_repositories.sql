select
  name,
  repository_full_name,
  (repository ->> 'private') as repository_private
from
  github_package
where
  organization = 'turbot'
  and (repository ->> 'private')::bool = true;