select
  uid,
  display_name,
  a ->> 'service' as allowed_service
from
  gcp_apikeys_key,
  jsonb_array_elements(restrictions -> 'apiTargets') as a
where
  restrictions is not null;