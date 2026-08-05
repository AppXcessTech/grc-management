select
  name,
  metric ->> 'Id' as metric_id,
  metric ->> 'Expression' as metric_expression,
  metric -> 'MetricStat' -> 'Metric' ->> 'MetricName' as metric_name,
  metric -> 'MetricStat' -> 'Metric' ->> 'Namespace' as metric_namespace,
  metric -> 'MetricStat' -> 'Metric' ->> 'Dimensions' as metric_dimensions,
  metric ->> 'ReturnData' as metric_return_data
from
  aws_cloudwatch_alarm,
  jsonb_array_elements(metrics) as metric;