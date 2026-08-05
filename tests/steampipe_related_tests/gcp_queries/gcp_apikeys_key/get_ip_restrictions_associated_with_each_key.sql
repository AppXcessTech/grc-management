select
  uid,
  display_name,
  a as allowed_ip
from
  gcp_apikeys_key,
  jsonb_array_elements_text(restrictions -> 'serverKeyRestrictions' -> 'allowedIps') as a
where
  restrictions is not null;