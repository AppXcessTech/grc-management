select
  machine_type_name,
  count(*) as count
from
  gcp_compute_instance
group by
  machine_type_name
order by
  count desc;