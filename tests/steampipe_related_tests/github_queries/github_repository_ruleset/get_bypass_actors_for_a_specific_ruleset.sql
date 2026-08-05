select
  name,
  b ->>'id' as bypass_actor_id,
  b ->>'deploy_key' as deploy_key,
  b ->>'bypass_mode' as bypass_mode,
  b ->>'repository_role_name' as repository_role_name,
  b ->>'repository_role_database_id' as repository_role_database_id
from
  github_repository_ruleset,
  jsonb_array_elements(bypass_actors) as b
where
  repository_full_name = 'pro-cloud-49/test-rule'
  and name = 'test34';