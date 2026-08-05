select
  name,
  description,
  client,
  client_version,
  create_time,
  ingress
from
  gcp_cloud_run_service
where
  ingress = 'INGRESS_TRAFFIC_ALL';