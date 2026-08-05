select
  organization,
  login,
  role,
  has_two_factor_enabled
from
  github_organization_member
where
  organization = 'my_org'
  and role = 'ADMIN'
  and not has_two_factor_enabled;