select
  r -> 'Tags' ->> 'Environment' as environment,
  count(r ->> 'Tags')
from
  aws_securityhub_finding as f,
  jsonb_array_elements(resources) as r
group by
  r -> 'Tags' ->> 'Environment'
order by
  count desc;