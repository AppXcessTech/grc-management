select
  uid,
  display_name,
  a as allowed_website
from
  gcp_apikeys_key,
  jsonb_array_elements_text(restrictions -> 'browserKeyRestrictions' -> 'allowedReferrers') as a
where
  restrictions is not null;