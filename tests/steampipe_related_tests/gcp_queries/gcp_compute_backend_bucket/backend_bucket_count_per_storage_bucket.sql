select
  bucket_name,
  count(*) as backend_bucket_count
from
  gcp_compute_backend_bucket
group by
  bucket_name;