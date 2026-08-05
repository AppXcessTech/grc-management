select
  name,
  create_time,
  creator,
  launch_stage
from
  gcp_cloud_run_job
where
  create_time >= now() - interval '30' day;