select
  r.name_with_owner as repository_full_name,
  v.name,
  v.value,
  v.updated_at
from
  github_my_repository r
  left join github_actions_repository_variable v on r.name_with_owner = v.repository_full_name
order by
  r.name_with_owner, v.name;