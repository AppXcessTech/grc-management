select
  title,
  id,
  patch_summary ->> 'Id' as patch_id,
  patch_summary ->> 'FailedCount' as failed_count,
  patch_summary ->> 'InstalledCount' as installed_count,
  patch_summary ->> 'InstalledOtherCount' as installed_other_count,
  patch_summary ->> 'InstalledPendingReboot' as installed_pending_reboot,
  patch_summary ->> 'InstalledRejectedCount' as installed_rejected_count,
  patch_summary ->> 'MissingCount' as missing_count,
  patch_summary ->> 'Operation' as operation,
  patch_summary ->> 'OperationEndTime' as operation_end_time,
  patch_summary ->> 'OperationStartTime' as operation_start_time,
  patch_summary ->> 'RebootOption' as reboot_option
from
  aws_securityhub_finding
where
  title = 'EC2 instance involved in SSH brute force attacks.';