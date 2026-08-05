select
  name,
  repository ->> 'name' as repository_name,
  repository ->> 'id' as repository_id,
  repository ->> 'private' as repository_private,
  repository ->> 'html_url' as repository_html_url,
  repository ->> 'description' as repository_description,
  repository ->> 'fork' as repository_fork,
  repository -> 'owner' ->> 'login' as repository_owner_login,
  repository ->> 'stargazers_url' as repository_stargazers_url,
  repository ->> 'contents_url' as repository_contents_url
from
  github_package
where
  organization = 'turbot';