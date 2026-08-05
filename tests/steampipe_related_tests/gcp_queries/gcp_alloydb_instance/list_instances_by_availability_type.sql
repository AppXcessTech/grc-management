select
  name,
  availability_type,
  state
from
  gcp_alloydb_instance
where
  availability_type = 'REGIONAL';