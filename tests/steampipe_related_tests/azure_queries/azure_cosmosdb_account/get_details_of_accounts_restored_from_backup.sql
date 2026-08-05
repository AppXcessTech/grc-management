select
  name,
  restore_parameters ->> 'restoreMode' as restore_mode,
  restore_parameters ->> 'restoreSource' as restore_source,
  d ->> 'databaseName' as restored_database_name,
  c as restored_collection_name
from
  azure_cosmosdb_account,
  jsonb_array_elements(restore_parameters -> 'databasesToRestore') d,
  jsonb_array_elements_text(d -> 'collectionNames') c;