from sqlalchemy.orm import DeclarativeBase


# Modern approach (SQLAlchemy 2.0+)
class Base(DeclarativeBase):
    pass


# Register the models for Migration
from . import enums  # noqa: E402, F401
from . import organization  # noqa: E402, F401
from . import department  # noqa: E402, F401
from . import business_unit  # noqa: E402, F401
from . import subsidiary  # noqa: E402, F401
from . import user  # noqa: E402, F401
from . import role  # noqa: E402, F401
from . import permission  # noqa: E402, F401
from . import role_permission  # noqa: E402, F401
from . import user_role  # noqa: E402, F401
from . import user_invitation  # noqa: E402, F401
from . import sso_configuration  # noqa: E402, F401
from . import audit_log  # noqa: E402, F401
from . import asset  # noqa: E402, F401
from . import asset_category  # noqa: E402, F401
from . import asset_tag  # noqa: E402, F401
from . import asset_owner  # noqa: E402, F401
from . import vendor  # noqa: E402, F401
from . import platform_user  # noqa: E402, F401
from . import platform_role  # noqa: E402, F401
from . import platform_permission  # noqa: E402, F401
from . import platform_user_role  # noqa: E402, F401
from . import platform_role_permission  # noqa: E402, F401
from . import platform_audit_log  # noqa: E402, F401

from . import framework  # noqa: E402, F401
from . import requirement  # noqa: E402, F401
from . import control  # noqa: E402, F401
from . import control_mapping  # noqa: E402, F401
from . import evidence  # noqa: E402, F401
from . import policy  # noqa: E402, F401
from . import policy_version  # noqa: E402, F401
from . import policy_review  # noqa: E402, F401
from . import policy_acknowledgement  # noqa: E402, F401
from . import password_reset_token  # noqa: E402, F401
from . import asset_import_request  # noqa: E402, F401
from . import asset_suggestion  # noqa: E402, F401
from . import notification  # noqa: E402, F401
from . import people_asset  # noqa: E402, F401
from . import people_asset_review  # noqa: E402, F401
from . import endpoint_device  # noqa: E402, F401
from . import compute_asset  # noqa: E402, F401
from . import raw_resource  # noqa: E402, F401
from . import canonical_asset  # noqa: E402, F401
from . import asset_relationship  # noqa: E402, F401
from . import refresh_token  # noqa: E402, F401
from . import raw_api_response  # noqa: E402, F401
