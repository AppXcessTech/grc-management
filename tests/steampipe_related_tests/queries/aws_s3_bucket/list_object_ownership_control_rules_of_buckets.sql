select
  b.name,
  r ->> 'ObjectOwnership' as object_ownership
from
  aws_s3_bucket as b,
  jsonb_array_elements(object_ownership_controls -> 'Rules') as r;