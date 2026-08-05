select
  name,
  account_name,
  throughput_settings ->> 'Name' as name,
  throughput_settings ->> 'ResourceThroughput' as throughput,
  throughput_settings ->> 'AutoscaleSettingsMaxThroughput' as maximum_throughput,
  throughput_settings ->> 'ResourceMinimumThroughput' as minimum_throughput,
  throughput_settings ->> 'ID' as id
from
  azure_cosmosdb_mongo_database;