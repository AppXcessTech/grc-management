select
  o.login as organization,
  v.name,
  v.value,
  v.visibility
from
  github_my_organization o
  left join github_actions_organization_variable v on o.login = v.organization
order by
  o.login, v.name;