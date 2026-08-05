select
  severity,
  count(severity)
from
  aws_inspector2_finding
group by
  severity
order by
  severity;