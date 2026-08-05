select
  name,
  id,
  source_project
from
  gcp_compute_image
where
  source_project = project;