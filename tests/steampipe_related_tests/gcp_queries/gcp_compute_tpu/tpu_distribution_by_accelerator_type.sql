select
  accelerator_type,
  count(*) as count,
  array_agg(name) as tpu_names
from
  gcp_compute_tpu
group by
  accelerator_type;