select
  guid,
  user_login,
  saml_identity ->> 'username' as saml_user,
  scim_identity ->> 'username' as scim_user,
  organization_invitation ->> 'role' as invited_role
from
  github_organization_external_identity
where
  organization = 'turbot';