select
  severity ->> 'Original' as severity_original,
  count(severity ->> 'Original')
from
  aws_securityhub_finding
group by
  severity ->> 'Original'
order by
  severity ->> 'Original';