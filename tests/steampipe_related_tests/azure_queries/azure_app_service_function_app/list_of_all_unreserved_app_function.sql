select
  name,
  reserved,
  resource_group
from
  azure_app_service_function_app
where
  not reserved;