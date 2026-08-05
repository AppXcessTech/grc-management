select
  instance_type,
  count(name)
from
  gcp_bigtable_instance
group by
  instance_type;