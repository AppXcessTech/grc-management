select
  id,
  instance_name,
  e ->> 'code' as error_code,
  e ->> 'message' as error_message
from
  gcp_sql_backup,
  jsonb_array_elements(error) as e
where
  status = 'FAILED';