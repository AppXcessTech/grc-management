select
  name,
  (owner ->> 'login') as owner_login,
  (owner ->> 'id') as owner_id,
  (owner ->> 'url') as owner_url,
  (owner ->> 'html_url') as owner_html_url
from
  github_package
where
  organization = 'turbot';