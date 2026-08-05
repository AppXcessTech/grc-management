select
  name,
  id,
  min_tls_version
from
  gcp_compute_ssl_policy
where
  min_tls_version = 'TLS_1_2'
  and profile = 'MODERN';