select
  launch_stage,
  count(*)
from
  gcp_cloud_run_job
group by
  launch_stage;