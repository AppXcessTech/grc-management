select
  name,
  id,
  image_encryption_key
from
  gcp_compute_image
where
  image_encryption_key is null;