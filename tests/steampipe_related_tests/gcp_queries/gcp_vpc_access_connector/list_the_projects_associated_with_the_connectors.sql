select
  name,
  jsonb_array_elements_text(connected_projects) as project_name,
  network,
  location
from
  gcp_vpc_access_connector
where
  connected_projects is not null;