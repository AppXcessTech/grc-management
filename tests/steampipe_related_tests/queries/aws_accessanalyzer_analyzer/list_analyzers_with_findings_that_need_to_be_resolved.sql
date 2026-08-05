select
  a.arn as analyzer_arn,
  a.name as analyzer_name,
  a.region as analyzer_region,
  a.account_id,
  count(f.id) as findings_count
from
  aws_accessanalyzer_analyzer as a
  join aws_accessanalyzer_finding as f on f.access_analyzer_arn = a.arn
where
  a.status = 'ACTIVE'
group by
  a.arn,
  a.name,
  a.region,
  a.account_id
having
  count(f.id) > 0;