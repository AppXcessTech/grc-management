select
  name as repository,
  hook
from
  github_my_repository,
  jsonb_array_elements(hooks) as hook
where
  hook -> 'config' ->> 'insecure_ssl' = '1'
  or hook -> 'config' ->> 'secret' is null
  or hook -> 'config' ->> 'url' not like '%https:%';