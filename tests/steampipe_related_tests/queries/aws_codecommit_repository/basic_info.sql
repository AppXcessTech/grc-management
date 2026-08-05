select
  repository_name,
  repository_id,
  arn,
  creation_date,
  region
from
  aws_codecommit_repository;