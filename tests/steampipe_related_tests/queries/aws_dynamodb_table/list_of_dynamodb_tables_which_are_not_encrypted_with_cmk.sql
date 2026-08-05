select
  name,
  sse_description
from
  aws_dynamodb_table
where
  sse_description is null;