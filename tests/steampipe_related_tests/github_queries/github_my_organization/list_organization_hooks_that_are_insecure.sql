select
  login as organization,
  hook
from
  github_my_organization,
  jsonb_array_elements(hooks) as hook
where
  hook -> 'config' ->> 'insecure_ssl' = '1'
  or hook -> 'config' ->> 'secret' is null
  or hook -> 'config' ->> 'url' not like '%https:%';