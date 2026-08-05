select
  project_id,
  parent ->> 'id' as parent_id,
  parent ->> 'type' as parent_type,
  case when jsonb_array_length(ancestors) > 1 then ancestors -> -1 -> 'resourceId' ->> 'id' else null end as organization_id
from
  gcp_project;