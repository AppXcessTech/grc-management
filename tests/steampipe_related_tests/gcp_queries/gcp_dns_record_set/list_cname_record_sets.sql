select
  name,
  managed_zone_name,
  type,
  ttl
from
  gcp_dns_record_set
where
 type = 'CNAME';