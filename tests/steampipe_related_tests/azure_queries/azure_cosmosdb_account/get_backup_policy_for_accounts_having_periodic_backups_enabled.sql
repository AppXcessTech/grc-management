select
  name,
  region,
  backup_policy -> 'periodicModeProperties' ->> 'backupIntervalInMinutes' as backup_interval_mins,
  backup_policy -> 'periodicModeProperties' ->> 'backupRetentionIntervalInHours' as backup_retention_interval_hrs,
  backup_policy -> 'periodicModeProperties' ->> 'backupStorageRedundancy' as backup_storage_redundancy
from
  azure_cosmosdb_account
where
  backup_policy ->> 'type' = 'Periodic';