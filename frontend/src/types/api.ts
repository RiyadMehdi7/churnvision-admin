// Enums matching backend
export enum TenantStatus {
    TRIAL = "TRIAL",
    ACTIVE = "ACTIVE",
    SUSPENDED = "SUSPENDED",
    CHURNED = "CHURNED",
}

export enum PricingTier {
    STARTER = "STARTER",
    PROFESSIONAL = "PROFESSIONAL",
    ENTERPRISE = "ENTERPRISE",
}

export enum ReleaseTrack {
    STABLE = "STABLE",
    BETA = "BETA",
    LTS = "LTS",
}

export enum ReleaseStatus {
    DRAFT = "DRAFT",
    PUBLISHED = "PUBLISHED",
    DEPRECATED = "DEPRECATED",
}

export enum InvoiceStatus {
    DRAFT = "DRAFT",
    SENT = "SENT",
    PAID = "PAID",
    OVERDUE = "OVERDUE",
    VOID = "VOID",
}

export enum SubscriptionStatus {
    ACTIVE = "ACTIVE",
    PAST_DUE = "PAST_DUE",
    CANCELLED = "CANCELLED",
}

export enum ContractStatus {
    ACTIVE = "ACTIVE",
    PENDING_RENEWAL = "PENDING_RENEWAL",
    EXPIRED = "EXPIRED",
}

// Tenant types
export interface TenantContact {
    id: string;
    tenant_id: string;
    name: string;
    email: string;
    role?: string;
    phone?: string;
}

export interface Tenant {
    id: string;
    name: string;
    slug: string;
    status: TenantStatus;
    tier: PricingTier;
    max_employees?: number;
    max_users: number;
    features_enabled: string[];
    industry?: string;
    region?: string;
    created_at: string;
    contacts: TenantContact[];
}

export interface TenantCreate {
    name: string;
    slug: string;
    email_contact?: string;
    industry?: string;
    region?: string;
    tier?: PricingTier;
    max_employees?: number;
    max_users?: number;
    expiration_days?: number;
}

export interface TenantUpdate {
    name?: string;
    status?: TenantStatus;
    tier?: PricingTier;
    max_employees?: number;
    max_users?: number;
    features_enabled?: string[];
}

// Release types
export interface Release {
    id: string;
    version: string;
    track: ReleaseTrack;
    status: ReleaseStatus;
    docker_images: string[];
    requires_downtime: boolean;
    breaking_changes: string[];
    release_notes?: string;
    published_at?: string;
    created_at: string;
}

export interface ReleaseCreate {
    version: string;
    track?: ReleaseTrack;
    status?: ReleaseStatus;
    docker_images?: string[];
    requires_downtime?: boolean;
    breaking_changes?: string[];
    release_notes?: string;
}

export interface ReleaseUpdate {
    status?: ReleaseStatus;
    docker_images?: string[];
    release_notes?: string;
}

// License types
export interface License {
    id: string;
    tenant_id: string;
    key_string: string;
    issued_at: string;
    expires_at: string;
    revoked: boolean;
}

// Embedded keys for license JWT claims
export interface LLMApiKeys {
    openai?: string;
    anthropic?: string;
    google?: string;
}

export interface EmbeddedKeys {
    admin_api_key?: string;
    llm_api_keys?: LLMApiKeys;
}

export interface LicenseCreate {
    tenant_id: string;
    expiration_days?: number;
    max_employees?: number;
    max_users?: number;
    features?: string[];
    // Keys to embed in the license JWT for customer use
    embedded_keys?: EmbeddedKeys;
}

// Billing types
export interface Subscription {
    id: string;
    tenant_id: string;
    plan: string;
    status: SubscriptionStatus;
    base_price: number;
    currency: string;
    payment_method: string;
    billing_cycle_start: string;
    next_invoice_date: string;
}

export interface SubscriptionCreate {
    tenant_id: string;
    plan?: string;
    base_price: number;
    currency?: string;
    payment_method?: string;
    start_date?: string;
}

export interface Invoice {
    id: string;
    tenant_id: string;
    subscription_id?: string;
    invoice_number: string;
    subtotal: number;
    tax: number;
    total: number;
    currency: string;
    due_date: string;
    status: InvoiceStatus;
    paid_at?: string;
    pdf_url?: string;
}

export interface InvoiceCreate {
    tenant_id: string;
    subscription_id?: string;
    invoice_number: string;
    subtotal: number;
    tax: number;
    total: number;
    currency: string;
    due_date: string;
    status: InvoiceStatus;
    line_items?: { description: string; amount: number; quantity?: number }[];
}

// Contract types
export interface Contract {
    id: string;
    tenant_id: string;
    contract_type: string;
    start_date: string;
    end_date: string;
    auto_renew: boolean;
    notice_period_days: number;
    total_contract_value: number;
    payment_terms: string;
    document_url?: string;
    status: ContractStatus;
    renewal_reminder_sent: boolean;
}

export interface ContractCreate {
    tenant_id: string;
    contract_type?: string;
    start_date: string;
    end_date: string;
    auto_renew?: boolean;
    notice_period_days?: number;
    total_contract_value: number;
    payment_terms?: string;
    document_url?: string;
}

// Support types
export interface Ticket {
    id: string;
    tenant_id: string;
    subject: string;
    description: string;
    priority: string;
    status: string;
    created_at: string;
}

export interface TicketCreate {
    tenant_id: string;
    subject: string;
    description: string;
    priority?: string;
}

export interface Announcement {
    id: string;
    title: string;
    content: string;
    published_at: string;
    expires_at?: string;
}

export interface AnnouncementCreate {
    title: string;
    content: string;
    expires_at?: string;
}

// Dashboard stats types
export interface DashboardStats {
    total_tenants: number;
    active_tenants: number;
    trial_tenants: number;
    mrr: number;
    latest_version: string;
    tenants_on_latest: number;
    expiring_licenses_count: number;
    overdue_invoices_count: number;
    deprecated_version_tenants: number;
}

export interface ActivityItem {
    id: string;
    tenant_name: string;
    action: string;
    timestamp: string;
}
