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
  parent = 'C046psxkn'
  and create_time > now() - interval '7' day;