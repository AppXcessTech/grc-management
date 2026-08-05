select
  name,
  display_name,
  dynamic_group_metadata ->> 'Status' as dynamic_group_status,
  queries ->> 'Query' as dynamic_group_query,
  queries ->> 'ResourceType' as dynamic_group_query_resource_type,
  project
from
  gcp_cloud_identity_group,
  jsonb_array_elements(dynamic_group_metadata -> 'Queries') as queries
where
  parent = 'C046psxkn';