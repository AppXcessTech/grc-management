select
  name,
  id,
  enable_logging
from
  gcp_dns_policy
where
  not enable_logging;