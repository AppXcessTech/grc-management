select
  name,
  https_only,
  kind,
  region
from
  azure_app_service_function_app
where
  not https_only;