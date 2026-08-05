select
  name,
  display_name,
  is_cluster
from
  gcp_monitoring_group
where
  is_cluster;