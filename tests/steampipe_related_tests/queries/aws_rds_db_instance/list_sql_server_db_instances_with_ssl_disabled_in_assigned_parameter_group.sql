with db_parameter_group as (
  select
    name as db_parameter_group_name,
    pg ->> 'ParameterName' as parameter_name,
    pg ->> 'ParameterValue' as parameter_value
  from
    aws_rds_db_parameter_group,
    jsonb_array_elements(parameters) as pg
  where
    -- The example is limited to SQL Server, this may change based on DB engine
    pg ->> 'ParameterName' like 'rds.force_ssl'
    and name not like 'default.%'
),
 rds_associated_parameter_group as (
  select
    db_instance_identifier as db_instance_identifier,
    arn,
    pg ->> 'DBParameterGroupName' as DBParameterGroupName
  from
    aws_rds_db_instance,
    jsonb_array_elements(db_parameter_groups) as pg
  where
    engine like 'sqlserve%'
)
select
  rds.db_instance_identifier as name,
  rds.DBParameterGroupName,
  parameter_name,
  parameter_value
from
  rds_associated_parameter_group as rds
  left join db_parameter_group d on rds.DBParameterGroupName = d.db_parameter_group_name
where
  parameter_value = '0'