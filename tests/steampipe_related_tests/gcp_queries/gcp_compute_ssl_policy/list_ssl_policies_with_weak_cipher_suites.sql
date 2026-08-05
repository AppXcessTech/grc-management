select
  name,
  id,
  enabled_feature
from
  gcp_compute_ssl_policy,
  jsonb_array_elements_text(enabled_features) as enabled_feature
where
  profile = 'CUSTOM'
  and enabled_feature in('TLS_RSA_WITH_AES_128_GCM_SHA256', 'TLS_RSA_WITH_AES_256_GCM_SHA384', 'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_RSA_WITH_AES_256_CBC_SHA', 'TLS_RSA_WITH_3DES_EDE_CBC_SHA');