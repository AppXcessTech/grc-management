select
  bucket,
  count(*) as total_objects,
  sum(size) as total_size_bytes
from
  gcp_storage_object o,
  gcp_storage_bucket b
where
  o.bucket = b.name
group by
  bucket;