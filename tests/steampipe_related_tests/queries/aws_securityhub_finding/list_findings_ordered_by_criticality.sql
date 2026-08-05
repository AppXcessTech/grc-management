select
  title,
  product_arn,
  product_name,
  criticality
from
  aws_securityhub_finding
order by
  criticality desc nulls last;