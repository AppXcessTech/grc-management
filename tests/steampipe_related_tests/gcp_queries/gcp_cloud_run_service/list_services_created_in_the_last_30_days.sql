select
  name,
  description,
  create_time,
  creator,
  launch_stage
from
  gcp_cloud_run_service
where
  create_time >= now() - interval '30' day;