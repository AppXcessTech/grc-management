select
  name,
  id
from
  gcp_compute_image
where
  tags -> 'owner' is null
  and  source_project = project;