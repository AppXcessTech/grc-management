select
  repository_name,
  encryption_configuration ->> 'EncryptionType' as encryption_type,
  encryption_configuration ->> 'KmsKey' as kms_key
from
  aws_ecr_repository
where
  encryption_configuration ->> 'EncryptionType' = 'AES256';