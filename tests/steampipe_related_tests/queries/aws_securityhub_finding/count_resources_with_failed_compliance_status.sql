select
  r ->> 'Type' as resource_type,
  count(r ->> 'Type')
from
  aws_securityhub_finding,
  jsonb_array_elements(resources) as r
group by
  r ->> 'Type'
order by
  count desc;