select
  address,
  address_type,
  creation_timestamp,
  status
from
  gcp_compute_address where status != 'IN_USE' ;