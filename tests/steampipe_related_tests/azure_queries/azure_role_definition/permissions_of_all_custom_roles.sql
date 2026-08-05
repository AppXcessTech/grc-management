select
  name,
  role_name,
  role_type,
  permission -> 'actions' as action,
  permission -> 'dataActions' as data_action,
  permission -> 'notActions' as no_action,
  permission -> 'notDataActions' as not_data_actions
from
  azure_role_definition
  cross join jsonb_array_elements(permissions) as permission
where
  role_type = 'CustomRole';