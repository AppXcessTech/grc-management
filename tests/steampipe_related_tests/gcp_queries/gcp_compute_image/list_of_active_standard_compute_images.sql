select
  name,
  id,
  source_project
from
  gcp_compute_image
where
  deprecation_state = 'ACTIVE'
  and source_project != project;