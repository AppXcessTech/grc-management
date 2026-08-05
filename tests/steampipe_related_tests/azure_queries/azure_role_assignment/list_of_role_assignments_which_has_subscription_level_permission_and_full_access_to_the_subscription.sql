select
  ra.name as roll_assignment_name,
  rd.role_name
from
  azure_role_assignment ra
  join azure_role_definition rd on ra.role_definition_id = rd.id
  cross join jsonb_array_elements(rd.permissions) as perm
where
  ra.scope like '/subscriptions/%'
  and perm -> 'actions' = '["*"]';