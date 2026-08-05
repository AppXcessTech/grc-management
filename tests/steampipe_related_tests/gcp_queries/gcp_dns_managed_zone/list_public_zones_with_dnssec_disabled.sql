select
  name,
  id,
  dns_name,
  dnssec_config_state,
  visibility
from
  gcp_dns_managed_zone
where 
  visibility = 'public'
  and 
  (
    dnssec_config_state is null
    or dnssec_config_state = 'off'
  );