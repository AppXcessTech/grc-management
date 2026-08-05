select
  os_type,
  count(name) as group_count
from
  azure_container_group
group by
  os_type;