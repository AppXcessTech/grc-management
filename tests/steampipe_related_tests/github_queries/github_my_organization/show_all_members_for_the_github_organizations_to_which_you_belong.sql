select
  o.login as organization,
  m.login as member_login
from
  github_my_organization o
  join github_organization_member m on o.login = m.organization;