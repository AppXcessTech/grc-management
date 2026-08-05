select
  o.login as org,
  o.saml_identity_provider ->> 'sso_url' as sso_url,
  e.user_login,
  e.user_detail ->> 'email' as user_email,
  e.saml_identity ->> 'username' as saml_user,
  e.scim_identity ->> 'username' as scim_user,
  e.organization_invitation ->> 'role' as invited_role
from
  github_my_organization o
join
  github_organization_external_identity e
on
  o.login = e.organization;