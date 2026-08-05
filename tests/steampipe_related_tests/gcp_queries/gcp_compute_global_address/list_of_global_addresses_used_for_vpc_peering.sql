select
  name,
  address,
  purpose
from
  gcp_compute_global_address
where
  purpose = 'VPC_PEERING';