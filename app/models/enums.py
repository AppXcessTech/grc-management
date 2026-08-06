from enum import Enum as PyEnum


class OrganizationSize(str, PyEnum):
    startup = "startup"
    SMB = "SMB"
    enterprise = "enterprise"


class SubscriptionTier(str, PyEnum):
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class UserStatus(str, PyEnum):
    invited = "invited"
    active = "active"
    suspended = "suspended"
    deactivated = "deactivated"


class RoleName(str, PyEnum):
    super_admin = "super_admin"
    compliance_admin = "compliance_admin"
    security_manager = "security_manager"
    auditor = "auditor"
    employee = "employee"
    vendor_user = "vendor_user"
    read_only = "read_only"


class PermissionAction(str, PyEnum):
    view = "view"
    create = "create"
    edit = "edit"
    delete = "delete"
    approve = "approve"
    bulk_import = "bulk_import"
    map = "map"
    acknowledge = "acknowledge"
    upload = "upload"
    export = "export"
    configure = "configure"
    resolve = "resolve"
    plan = "plan"
    conduct = "conduct"
    findings = "findings"
    remediate = "remediate"
    close = "close"
    score = "score"
    treat = "treat"
    upload_docs = "upload_docs"
    manage_templates = "manage_templates"
    manage_answers = "manage_answers"
    respond = "respond"


class SSOProvider(str, PyEnum):
    SAML = "SAML"
    OIDC = "OIDC"
    Google = "Google"
    Azure = "Azure"
    Microsoft = "Microsoft"


class InvitationStatus(str, PyEnum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"


class AssetType(str, PyEnum):
    employee = "employee"
    device = "device"
    server = "server"
    application = "application"
    database = "database"
    cloud_resource = "cloud_resource"
    vendor = "vendor"


class AssetCriticality(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AssetRiskLevel(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IntegrationProvider(str, PyEnum):
    Azure_AD = "Azure AD"
    Google_Workspace = "Google Workspace"
    Microsoft_365 = "Microsoft 365"
    AWS = "AWS"
    GCP = "GCP"
    Azure = "Azure"



class ComplianceStatus(str, PyEnum):
    specified = "specified"
    in_draft = "in_draft"
    done = "done"
    compliant = "compliant"
    non_compliant = "non_compliant"
    in_progress = "in_progress"
    not_applicable = "not_applicable"


class PolicyCategory(str, PyEnum):
    information_security = "information_security"
    access_control = "access_control"
    incident_response = "incident_response"
    data_retention = "data_retention"
    vendor_security = "vendor_security"
    change_management = "change_management"
    other = "other"


class PolicyStatus(str, PyEnum):
    draft = "draft"
    published = "published"
    archived = "archived"


class ReviewStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class EvidenceSourceType(str, PyEnum):
    manual = "manual"
    aws = "aws"
    azure = "azure"
    gcp = "gcp"
    github = "github"
    gitlab = "gitlab"
    jira = "jira"
    okta = "okta"
    google_workspace = "google_workspace"


class EvidenceType(str, PyEnum):
    screenshot = "screenshot"
    log = "log"
    configuration = "configuration"
    report = "report"
    api_snapshot = "api_snapshot"
    document = "document"


class EvidenceReviewStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CanonicalType(str, PyEnum):
    identity = "Identity"
    group = "Group"
    role = "Role"
    service_account = "ServiceAccount"
    # Authentication policies (password policy, MFA, sign-on, etc.) and IAM
    # policies all share one canonical category: Policy.
    policy = "Policy"
    compute = "Compute"
    serverless = "Serverless"
    container = "Container"
    container_registry = "ContainerRegistry"
    storage = "Storage"
    database = "Database"
    data_warehouse = "DataWarehouse"
    cache = "Cache"
    backup = "Backup"
    network = "Network"
    firewall = "Firewall"
    load_balancer = "LoadBalancer"
    dns = "DNS"
    vpn = "VPN"
    secret = "Secret"
    certificate = "Certificate"
    encryption_key = "EncryptionKey"
    logging = "Logging"
    monitoring = "Monitoring"
    threat_finding = "ThreatFinding"
    vulnerability = "Vulnerability"
    compliance_finding = "ComplianceFinding"
    application = "Application"
    repository = "Repository"
    pipeline = "Pipeline"
    deployment = "Deployment"
    artifact = "Artifact"
    webhook = "Webhook"
    configuration = "Configuration"
    organization = "Organization"
    package = "Package"
    device = "Device"
    mobile_device = "MobileDevice"
    endpoint_protection = "EndpointProtection"
    employee = "Employee"
    background_check = "BackgroundCheck"
    security_training = "SecurityTraining"
    policy_acknowledgement = "PolicyAcknowledgement"
    vendor = "Vendor"
    vendor_assessment = "VendorAssessment"
    nda = "NDA"
    ticket = "Ticket"
    custom = "Custom"
    unmapped = "Unmapped"
    other = "Other"


# Maps each CanonicalType to a UI group slug
ASSET_CATEGORIES: dict[str, str] = {
    "Identity": "identity-access",
    "Group": "identity-access",
    "Role": "identity-access",
    "ServiceAccount": "identity-access",
    "Policy": "identity-access",
    "Compute": "compute",
    "Serverless": "compute",
    "Container": "compute",
    "ContainerRegistry": "compute",
    "Storage": "storage-data",
    "Backup": "storage-data",
    "Database": "storage-data",
    "DataWarehouse": "storage-data",
    "Cache": "storage-data",
    "Network": "networking",
    "Firewall": "networking",
    "LoadBalancer": "networking",
    "DNS": "networking",
    "VPN": "networking",
    "Secret": "security",
    "Certificate": "security",
    "EncryptionKey": "security",
    "Logging": "security",
    "Monitoring": "security",
    "ThreatFinding": "security",
    "Vulnerability": "security",
    "ComplianceFinding": "security",
    "Application": "devops",
    "Repository": "devops",
    "Pipeline": "devops",
    "Deployment": "devops",
    "Artifact": "devops",
    "Webhook": "devops",
    "Configuration": "security",
    "Organization": "identity-access",
    "Package": "devops",
    "Device": "endpoint",
    "MobileDevice": "endpoint",
    "EndpointProtection": "endpoint",
    "Vendor": "third-party",
    "VendorAssessment": "third-party",
    "BackgroundCheck": "evidence",
    "SecurityTraining": "evidence",
    "PolicyAcknowledgement": "evidence",
    "NDA": "evidence",
    "Employee": "people",
    "Ticket": "workflow",
    "Custom": "other",
    "Unmapped": "other",
    "Other": "other",
}

CATEGORY_LABELS: dict[str, str] = {
    "identity-access": "Identity and Access",
    "compute": "Compute",
    "storage-data": "Storage & Data",
    "networking": "Networking",
    "security": "Security",
    "devops": "DevOps",
    "endpoint": "Endpoint",
    "third-party": "Third-Party",
    "evidence": "Evidence Resources",
    "people": "People",
    "workflow": "Workflow Resource",
    "other": "Other",
}

ASSET_CATEGORY_SLUGS: list[str] = [
    "identity-access", "compute", "storage-data", "networking",
    "security", "devops", "endpoint", "third-party",
    "evidence", "people", "workflow",
]


class RelationshipType(str, PyEnum):
    uses = "uses"
    attached_to = "attached_to"
    belongs_to = "belongs_to"
    inside = "inside"
    encrypted_by = "encrypted_by"
    member_of = "member_of"
    manages = "manages"
    depends_on = "depends_on"
    connects_to = "connects_to"
    routes_to = "routes_to"
    logs_to = "logs_to"
    monitors = "monitors"
    protects = "protects"
    contains = "contains"
    deployed_by = "deployed_by"
    runs_on = "runs_on"
    associated_with = "associated_with"


class Provider(str, PyEnum):
    aws = "AWS"
    azure = "Azure"
    gcp = "GCP"
    okta = "Okta"
    github = "GitHub"
    gitlab = "GitLab"
    slack = "Slack"
    crowdstrike = "CrowdStrike"
    intune = "Intune"
    manual = "Manual"
    other = "Other"
