select
  name,
  adaptive_protection_config
from
  gcp_compute_security_policy
where
  adaptive_protection_config -> 'layer7DdosDefenseConfig' ->> 'enable' = 'true';