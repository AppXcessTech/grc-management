select
  repository_name,
  image_tag_mutability
from
  aws_ecr_repository
where
  image_tag_mutability = 'IMMUTABLE';