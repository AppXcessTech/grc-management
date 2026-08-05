"""
Steampipe config management — intentionally empty.

The SteampipeConfigManager, SteampipeImportWorker, and ConfigWatchdog classes
previously defined here were dead code — never imported or used anywhere in the
application. Each integration (AWS, Azure, GitHub, Okta) manages its own
temporary config directory directly via tempfile.TemporaryDirectory().

This file is kept as a placeholder to avoid breaking any residual references.
"""