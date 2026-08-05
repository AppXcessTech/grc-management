select
  name,
  id,
  enable_flow_logs
from
  gcp_compute_subnetwork
where
  not enable_flow_logs;