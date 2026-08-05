select
  launch_stage,
  count(*)
from
  gcp_cloud_run_service
group by
  launch_stage;