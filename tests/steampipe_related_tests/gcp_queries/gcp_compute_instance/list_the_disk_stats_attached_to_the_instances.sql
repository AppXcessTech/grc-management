select
  name,
  count(d) as num_disks,
  sum( (d ->> 'diskSizeGb') :: int ) as total_storage
from
  gcp_compute_instance as i,
  jsonb_array_elements(disks) as d
group by
  name;