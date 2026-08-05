select
  name,
  display_name,
  description,
  create_time,
  location,
  project
from
  gcp_cloud_identity_group
where
  parent = 'C046psxkn';