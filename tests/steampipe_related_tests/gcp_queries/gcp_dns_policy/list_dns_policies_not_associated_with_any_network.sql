select
  name,
  id,
  networks
from
  gcp_dns_policy
where
  networks = '[]';