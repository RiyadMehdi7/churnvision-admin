import {
    Tenant,
    TenantCreate,
    TenantUpdate,
    Release,
    ReleaseCreate,
    ReleaseUpdate,
    License,
    LicenseCreate,
    Subscription,
    SubscriptionCreate,
    Invoice,
    InvoiceCreate,
    Contract,
    ContractCreate,
    Ticket,
    TicketCreate,
    Announcement,
    AnnouncementCreate,
    DashboardStats,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
        this.name = "ApiError";
    }
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new ApiError(error.detail || "Request failed", response.status);
    }

    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

// Tenant API
export const tenantApi = {
    list: (skip = 0, limit = 100) =>
        request<Tenant[]>(`/tenants/?skip=${skip}&limit=${limit}`),

    get: (slug: string) =>
        request<Tenant>(`/tenants/${slug}`),

    create: (data: TenantCreate) =>
        request<Tenant>("/tenants/", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    update: (slug: string, data: TenantUpdate) =>
        request<Tenant>(`/tenants/${slug}`, {
            method: "PUT",
            body: JSON.stringify(data),
        }),

    delete: (slug: string) =>
        request<void>(`/tenants/${slug}`, {
            method: "DELETE",
        }),
    
    downloadInstallPackage: async (slug: string, dockerImage?: string) => {
        const params = new URLSearchParams();
        if (dockerImage) params.set('docker_image', dockerImage);
        
        const url = `${API_BASE_URL}/tenants/${slug}/install-package${params.toString() ? `?${params}` : ''}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Download failed' }));
            throw new ApiError(error.detail || 'Download failed', response.status);
        }
        
        // Get the blob and trigger download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `churnvision-${slug}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
    },
};

// Release API
export const releaseApi = {
    list: (skip = 0, limit = 100) =>
        request<Release[]>(`/releases/?skip=${skip}&limit=${limit}`),

    get: (version: string) =>
        request<Release>(`/releases/${version}`),

    create: (data: ReleaseCreate) =>
        request<Release>("/releases/", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    update: (version: string, data: ReleaseUpdate) =>
        request<Release>(`/releases/${version}`, {
            method: "PUT",
            body: JSON.stringify(data),
        }),

    delete: (version: string) =>
        request<void>(`/releases/${version}`, {
            method: "DELETE",
        }),
};

// License API
export const licenseApi = {
    list: (skip = 0, limit = 100) =>
        request<License[]>(`/licenses/?skip=${skip}&limit=${limit}`),

    listByTenant: (tenantId: string) =>
        request<License[]>(`/licenses/tenant/${tenantId}`),

    create: (data: LicenseCreate) =>
        request<License>("/licenses/", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    revoke: (licenseId: string, reason?: string) =>
        request<License>(`/licenses/${licenseId}?reason=${encodeURIComponent(reason || "Revoked via UI")}`, {
            method: "DELETE",
        }),
};

// Billing API
export const billingApi = {
    createSubscription: (data: SubscriptionCreate) =>
        request<Subscription>("/billing/subscriptions", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    getSubscriptions: (tenantId?: string) =>
        request<Subscription[]>(`/billing/subscriptions${tenantId ? `/${tenantId}` : ''}`),

    createInvoice: (data: InvoiceCreate) =>
        request<Invoice>("/billing/invoices", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    getInvoices: (tenantId: string) =>
        request<Invoice[]>(`/billing/invoices/${tenantId}`),

    listAllInvoices: (status?: string) =>
        request<Invoice[]>(`/billing/invoices${status ? `?status=${status}` : ""}`),
};

// Contract API
export const contractApi = {
    list: () =>
        request<Contract[]>("/contracts/"),

    getByTenant: (tenantId: string) =>
        request<Contract[]>(`/contracts/${tenantId}`),

    create: (data: ContractCreate) =>
        request<Contract>("/contracts/", {
            method: "POST",
            body: JSON.stringify(data),
        }),
};

// Support API
export const supportApi = {
    listTickets: (tenantId?: string) =>
        request<Ticket[]>(`/support/tickets${tenantId ? `?tenant_id=${tenantId}` : ""}`),

    createTicket: (data: TicketCreate) =>
        request<Ticket>("/support/tickets", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    listAnnouncements: () =>
        request<Announcement[]>("/support/announcements"),

    createAnnouncement: (data: AnnouncementCreate) =>
        request<Announcement>("/support/announcements", {
            method: "POST",
            body: JSON.stringify(data),
        }),
};

// Dashboard API
export const dashboardApi = {
    getStats: () =>
        request<DashboardStats>("/dashboard/stats"),
};

export { ApiError };
