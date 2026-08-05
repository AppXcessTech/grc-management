select
  name,
  network,
  min_throughput,
  max_throughput
from
  gcp_vpc_access_connector
where
  network = 'default'
  and max_throughput >= 1000;