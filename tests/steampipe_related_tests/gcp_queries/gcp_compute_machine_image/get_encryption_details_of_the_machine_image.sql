select
  name,
  machine_image_encryption_key ->> 'KmsKeyName' as kms_key_name,
  machine_image_encryption_key ->> 'KmsKeyServiceAccount' as kms_key_service_account,
  machine_image_encryption_key ->> 'RawKey' as raw_key,
  machine_image_encryption_key ->> 'RsaEncryptedKey' as rsa_encrypted_key,
  machine_image_encryption_key ->> 'Sha256' as sha256
from
  gcp_compute_machine_image;