select
  name,
  state,
  project,
  location
from
  gcp_vpc_access_connector
where
  state = 'READY';