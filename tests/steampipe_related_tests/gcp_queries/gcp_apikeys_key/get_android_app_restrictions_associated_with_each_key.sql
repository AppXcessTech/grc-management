select
  uid,
  display_name,
  a as allowed_android_apps
from
  gcp_apikeys_key,
  jsonb_array_elements(restrictions -> 'androidKeyRestrictions' -> 'allowedApplications') as a
where
  restrictions is not null;