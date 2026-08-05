select
  cluster_name,
  cluster_uuid,
  state
from
  gcp_dataproc_cluster
where
  state = 'ERROR';