import React from 'react';
import { Fingerprint, Server, HardDrive, Network, Shield, Code, Monitor, Handshake, FileCheck, Users, Ticket, Building2, Building, Layers, Globe, UserCheck, Users2, UserCog, Key, ShieldCheck, Cpu, Box, Container, Dock, Lock, FileText, Activity, AlertTriangle, Bug, AppWindow, GitBranch, GitPullRequest, Package, Smartphone, Shield as ShieldIcon, Database, FolderOpen, Wifi, Settings, Building as BuildingIcon } from 'lucide-react';

export interface SidebarItem {
  label: string;
  slug: string;
  icon: React.ComponentType<{ size?: number }>;
  count?: number;
  path: string;
}

export interface SidebarGroup {
  label: string;
  slug: string;
  icon: React.ComponentType<{ size?: number }>;
  items: SidebarItem[];
}

export const SIDEBAR: SidebarGroup[] = [
  {
    label: 'Identity and Access', slug: 'identity-access', icon: Fingerprint,
    items: [
      { label: 'Organization', slug: 'organization', icon: Building2, path: '/organizations' },
      { label: 'Department', slug: 'department', icon: Building, path: '/organizations/departments' },
      { label: 'Business Unit', slug: 'business-unit', icon: Layers, path: '/organizations/business-units' },
      { label: 'Account / Subscription / Tenant', slug: 'account', icon: Globe, path: '/assets/identity-access/account' },
      { label: 'Identity', slug: 'Identity', icon: UserCheck, path: '/assets/identity-access/Identity' },
      { label: 'Group', slug: 'Group', icon: Users2, path: '/assets/identity-access/Group' },
      { label: 'Role', slug: 'Role', icon: UserCog, path: '/assets/identity-access/Role' },
      { label: 'Service Account / App Identity', slug: 'ServiceAccount', icon: Key, path: '/assets/identity-access/ServiceAccount' },
      // Authentication policies (password policy, MFA, sign-on) and IAM
      // policies share one category: Policy.
      { label: 'Policy', slug: 'Policy', icon: ShieldCheck, path: '/assets/identity-access/Policy' },
      { label: 'Organization', slug: 'Organization', icon: BuildingIcon, path: '/assets/identity-access/Organization' },
    ],
  },
  {
    label: 'Compute', slug: 'compute', icon: Server,
    items: [
      { label: 'Compute', slug: 'Compute', icon: Cpu, path: '/assets/compute/Compute' },
      { label: 'Serverless', slug: 'Serverless', icon: Box, path: '/assets/compute/Serverless' },
      { label: 'Container / K8s Cluster', slug: 'Container', icon: Container, path: '/assets/compute/Container' },
      { label: 'Container Registry', slug: 'ContainerRegistry', icon: Dock, path: '/assets/compute/ContainerRegistry' },
    ],
  },
  {
    label: 'Storage & Data', slug: 'storage-data', icon: HardDrive,
    items: [
      { label: 'Storage', slug: 'Storage', icon: HardDrive, path: '/assets/storage-data/Storage' },
      { label: 'Database', slug: 'Database', icon: Database, path: '/assets/storage-data/Database' },
      { label: 'Data Warehouse', slug: 'DataWarehouse', icon: FolderOpen, path: '/assets/storage-data/DataWarehouse' },
      { label: 'Cache', slug: 'Cache', icon: Cpu, path: '/assets/storage-data/Cache' },
      { label: 'Backup / Snapshot', slug: 'Backup', icon: HardDrive, path: '/assets/storage-data/Backup' },
    ],
  },
  {
    label: 'Networking', slug: 'networking', icon: Network,
    items: [
      { label: 'Network (VPC/Subnet)', slug: 'Network', icon: Network, path: '/assets/networking/Network' },
      { label: 'Firewall / Security Group', slug: 'Firewall', icon: Shield, path: '/assets/networking/Firewall' },
      { label: 'Load Balancer', slug: 'LoadBalancer', icon: Activity, path: '/assets/networking/LoadBalancer' },
      { label: 'DNS', slug: 'DNS', icon: Globe, path: '/assets/networking/DNS' },
      { label: 'VPN / Gateway', slug: 'VPN', icon: Wifi, path: '/assets/networking/VPN' },
    ],
  },
  {
    label: 'Security', slug: 'security', icon: Shield,
    items: [
      { label: 'Secret', slug: 'Secret', icon: Lock, path: '/assets/security/Secret' },
      { label: 'Certificate', slug: 'Certificate', icon: FileText, path: '/assets/security/Certificate' },
      { label: 'Encryption Key', slug: 'EncryptionKey', icon: Key, path: '/assets/security/EncryptionKey' },
      { label: 'Configuration', slug: 'Configuration', icon: Settings, path: '/assets/security/Configuration' },
      { label: 'Logging', slug: 'Logging', icon: FileText, path: '/assets/security/Logging' },
      { label: 'Monitoring / Alert', slug: 'Monitoring', icon: Activity, path: '/assets/security/Monitoring' },
      { label: 'Threat Finding', slug: 'ThreatFinding', icon: AlertTriangle, path: '/assets/security/ThreatFinding' },
      { label: 'Vulnerability', slug: 'Vulnerability', icon: Bug, path: '/assets/security/Vulnerability' },
      { label: 'Compliance Finding', slug: 'ComplianceFinding', icon: ShieldCheck, path: '/assets/security/ComplianceFinding' },
    ],
  },
  {
    label: 'DevOps', slug: 'devops', icon: Code,
    items: [
      { label: 'Application', slug: 'Application', icon: AppWindow, path: '/assets/devops/Application' },
      { label: 'Repository', slug: 'Repository', icon: GitBranch, path: '/assets/devops/Repository' },
      { label: 'Pipeline', slug: 'Pipeline', icon: GitPullRequest, path: '/assets/devops/Pipeline' },
      { label: 'Deployment', slug: 'Deployment', icon: GitBranch, path: '/assets/devops/Deployment' },
      { label: 'Artifact', slug: 'Artifact', icon: Package, path: '/assets/devops/Artifact' },
      { label: 'Package', slug: 'Package', icon: Package, path: '/assets/devops/Package' },
      { label: 'Webhook', slug: 'Webhook', icon: Activity, path: '/assets/devops/Webhook' },
    ],
  },
  {
    label: 'Endpoint', slug: 'endpoint', icon: Monitor,
    items: [
      { label: 'Device', slug: 'Device', icon: Monitor, path: '/assets/devices' },
      { label: 'Mobile Device', slug: 'MobileDevice', icon: Smartphone, path: '/assets/endpoint/MobileDevice' },
      { label: 'Endpoint Protection', slug: 'EndpointProtection', icon: ShieldIcon, path: '/assets/endpoint/EndpointProtection' },
    ],
  },
  {
    label: 'Third-Party', slug: 'third-party', icon: Handshake,
    items: [
      { label: 'Vendor', slug: 'Vendor', icon: Handshake, path: '/assets/third-party/Vendor' },
    ],
  },
  {
    label: 'Evidence Resources', slug: 'evidence', icon: FileCheck,
    items: [
      { label: 'Background Check', slug: 'BackgroundCheck', icon: FileCheck, path: '/assets/evidence/BackgroundCheck' },
      { label: 'Security Training', slug: 'SecurityTraining', icon: ShieldCheck, path: '/assets/evidence/SecurityTraining' },
      { label: 'Policy Acknowledgement', slug: 'PolicyAcknowledgement', icon: FileText, path: '/assets/evidence/PolicyAcknowledgement' },
      { label: 'Vendor Assessment', slug: 'VendorAssessment', icon: FileCheck, path: '/assets/evidence/VendorAssessment' },
      { label: 'NDA / Agreement', slug: 'NDA', icon: FileText, path: '/assets/evidence/NDA' },
    ],
  },
  {
    label: 'People', slug: 'people', icon: Users,
    items: [
      { label: 'Employee', slug: 'Employee', icon: Users, path: '/assets/people' },
    ],
  },
  {
    label: 'Workflow Resource', slug: 'workflow', icon: Ticket,
    items: [
      { label: 'Ticket / Task', slug: 'Ticket', icon: Ticket, path: '/assets/workflow/Ticket' },
    ],
  },
];
