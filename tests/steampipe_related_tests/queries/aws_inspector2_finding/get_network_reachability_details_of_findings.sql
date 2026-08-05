select
  arn,
  network_reachability_details -> 'NetworkPath' -> 'Steps' as network_pathsteps,
  network_reachability_details -> 'OpenPortRange' ->> 'Begin' as open_port_range_begin,
  network_reachability_details -> 'OpenPortRange' ->> 'End' as open_port_range_end,
  network_reachability_details -> 'Protocol' as protocol
from
  aws_inspector2_finding;