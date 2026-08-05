select
  name,
  id,
  location,
  feature_settings -> 'SplitHealthChecks' as split_health_checks,
  feature_settings -> 'UseContainerOptimizedOs' as use_container_optimized_os
from
  gcp_app_engine_application;