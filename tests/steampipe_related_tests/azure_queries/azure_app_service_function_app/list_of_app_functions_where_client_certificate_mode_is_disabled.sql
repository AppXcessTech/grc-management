select
  name,
  client_cert_enabled,
  kind,
  region
from
  azure_app_service_function_app
where
  not client_cert_enabled;