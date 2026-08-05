select
  uid,
  display_name,
  a as allowed_ios_bundle_id
from
  gcp_apikeys_key,
  jsonb_array_elements_text(restrictions -> 'iosKeyRestrictions' -> 'allowedBundleIds') as a
where
  restrictions is not null;