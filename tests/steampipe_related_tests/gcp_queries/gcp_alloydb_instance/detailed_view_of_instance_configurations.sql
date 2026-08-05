select
  name,
  machine_config,
  client_connection_config,
  ip_address
from
  gcp_alloydb_instance
where
  name = 'instance-12345';