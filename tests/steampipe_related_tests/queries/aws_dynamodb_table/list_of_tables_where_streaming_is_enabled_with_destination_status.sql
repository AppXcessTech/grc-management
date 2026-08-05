select
  name,
  d ->> 'StreamArn' as kinesis_stream_arn,
  d ->> 'DestinationStatus' as stream_status
from
  aws_dynamodb_table,
  jsonb_array_elements(streaming_destination -> 'KinesisDataStreamDestinations') as d