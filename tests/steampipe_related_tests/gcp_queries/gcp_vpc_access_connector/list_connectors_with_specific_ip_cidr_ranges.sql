select
  name,
  ip_cidr_range,
  network,
  location
from
  gcp_vpc_access_connector
where
  ip_cidr_range = '10.8.0.0/28';