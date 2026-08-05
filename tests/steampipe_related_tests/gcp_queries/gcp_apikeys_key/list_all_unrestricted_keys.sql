select
  uid,
  display_name,
  create_time,
  case when restrictions is null then 'Unrestricted' else 'Restricted' end as state
from
  gcp_apikeys_key
where
  restrictions is null;