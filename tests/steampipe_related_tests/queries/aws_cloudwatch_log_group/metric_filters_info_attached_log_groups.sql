select
  groups.name as log_group_name,
  metric.name as metric_filter_name,
  metric.filter_pattern,
  metric.metric_transformation_name,
  metric.metric_transformation_value
from
  aws_cloudwatch_log_group groups
  join aws_cloudwatch_log_metric_filter metric on groups.name = metric.log_group_name;