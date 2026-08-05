select
  name,
  t ->> 'Percent' as percent,
  t ->> 'Revision' as revision,
  t ->> 'Tag' as tag,
  t ->> 'Type' as type
from
  gcp_cloud_run_service,
  jsonb_array_elements(traffic) as t;