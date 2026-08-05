select
  source_account_id,
  count(*) as finding_count
from
  aws_securityhub_finding
group by
  source_account_id
order by
  source_account_id;