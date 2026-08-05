select
  file_system_id,
  size_in_bytes ->> 'Value' as data_size,
  size_in_bytes ->> 'Timestamp' as data_size_timestamp,
  size_in_bytes ->> 'ValueInIA' as data_size_infrequent_access_storage,
  size_in_bytes ->> 'ValueInStandard' as data_size_standard_storage
from
  aws_efs_file_system;