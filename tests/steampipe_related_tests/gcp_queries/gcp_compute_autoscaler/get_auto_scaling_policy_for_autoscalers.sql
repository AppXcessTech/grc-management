select
  title,
  autoscaling_policy ->> 'mode' as mode,
  autoscaling_policy -> 'cpuUtilization' ->> 'predictiveMethod' as cpu_utilization_method,
  autoscaling_policy -> 'cpuUtilization' ->> 'utilizationTarget' as cpu_utilization_target,
  autoscaling_policy ->> 'maxNumReplicas' as max_replicas,
  autoscaling_policy ->> 'minNumReplicas' as min_replicas,
  autoscaling_policy ->> 'coolDownPeriodSec' as cool_down_period_sec
from
  gcp_compute_autoscaler;