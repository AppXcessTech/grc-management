select
  accelerator_type,
  count(*) as count,
  array_agg(name) as tpu_names
from
  gcp_tpu_vm
group by
  accelerator_type;