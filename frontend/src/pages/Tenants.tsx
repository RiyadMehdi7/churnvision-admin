import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { tenantApi } from '../services/api';
import { Tenant, TenantCreate, TenantStatus, PricingTier } from '../types/api';

const statusColors: Record<TenantStatus, string> = {
    [TenantStatus.ACTIVE]: 'bg-green-100 text-green-800',
    [TenantStatus.TRIAL]: 'bg-blue-100 text-blue-800',
    [TenantStatus.SUSPENDED]: 'bg-yellow-100 text-yellow-800',
    [TenantStatus.CHURNED]: 'bg-red-100 text-red-800',
};

const Tenants = () => {
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newTenant, setNewTenant] = useState<TenantCreate>({
        name: '',
        slug: '',
        tier: PricingTier.STARTER,
        max_employees: undefined,
        max_users: 5,
    });

    const fetchTenants = async () => {
        try {
            setLoading(true);
            const data = await tenantApi.list();
            setTenants(data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch tenants:', err);
            setError('Failed to load tenants');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTenants();
    }, []);

    const handleCreateTenant = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setCreating(true);
            await tenantApi.create(newTenant);
            setShowCreateModal(false);
            setNewTenant({ name: '', slug: '', tier: PricingTier.STARTER, max_employees: undefined, max_users: 5 });
            await fetchTenants();
        } catch (err) {
            console.error('Failed to create tenant:', err);
            setError('Failed to create tenant');
        } finally {
            setCreating(false);
        }
    };

    const handleDeleteTenant = async (slug: string) => {
        if (!confirm('Are you sure you want to delete this tenant?')) return;
        try {
            await tenantApi.delete(slug);
            await fetchTenants();
        } catch (err) {
            console.error('Failed to delete tenant:', err);
            setError('Failed to delete tenant');
        }
    };

    const handleDownloadInstallPackage = async (slug: string) => {
        try {
            await tenantApi.downloadInstallPackage(slug);
        } catch (err) {
            console.error('Failed to download install package:', err);
            setError('Failed to download installation package. Make sure tenant has an active license.');
        }
    };

    const generateSlug = (name: string) => {
        return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Tenants</h1>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    + New Tenant
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                    <button onClick={() => setError(null)} className="float-right">&times;</button>
                </div>
            )}

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tier</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Region</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center">
                                    <div className="animate-pulse flex justify-center">
                                        <div className="h-4 bg-gray-200 rounded w-32"></div>
                                    </div>
                                </td>
                            </tr>
                        ) : tenants.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                    No tenants found. Create your first tenant to get started.
                                </td>
                            </tr>
                        ) : (
                            tenants.map((tenant) => (
                                <tr key={tenant.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="font-medium text-gray-900">{tenant.name}</div>
                                        <div className="text-sm text-gray-500">{tenant.slug}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[tenant.status]}`}>
                                            {tenant.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {tenant.tier}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {tenant.region || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                        <button
                                            onClick={() => handleDownloadInstallPackage(tenant.slug)}
                                            className="text-green-600 hover:text-green-900 inline-flex items-center"
                                            title="Download Installation Package"
                                        >
                                            <Download size={16} className="mr-1" />
                                            Install
                                        </button>
                                        <button className="text-blue-600 hover:text-blue-900">Edit</button>
                                        <button
                                            onClick={() => handleDeleteTenant(tenant.slug)}
                                            className="text-red-600 hover:text-red-900"
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create Tenant Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Create New Tenant</h2>
                        <form onSubmit={handleCreateTenant}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={newTenant.name}
                                        onChange={(e) => {
                                            const name = e.target.value;
                                            setNewTenant({
                                                ...newTenant,
                                                name,
                                                slug: generateSlug(name),
                                            });
                                        }}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Slug</label>
                                    <input
                                        type="text"
                                        required
                                        value={newTenant.slug}
                                        onChange={(e) => setNewTenant({ ...newTenant, slug: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Tier</label>
                                    <select
                                        value={newTenant.tier}
                                        onChange={(e) => setNewTenant({ ...newTenant, tier: e.target.value as PricingTier })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    >
                                        <option value={PricingTier.STARTER}>Starter</option>
                                        <option value={PricingTier.PROFESSIONAL}>Professional</option>
                                        <option value={PricingTier.ENTERPRISE}>Enterprise</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Industry (optional)</label>
                                    <input
                                        type="text"
                                        value={newTenant.industry || ''}
                                        onChange={(e) => setNewTenant({ ...newTenant, industry: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Region (optional)</label>
                                    <input
                                        type="text"
                                        value={newTenant.region || ''}
                                        onChange={(e) => setNewTenant({ ...newTenant, region: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Max Employees (leave empty for unlimited)</label>
                                    <input
                                        type="number"
                                        value={newTenant.max_employees || ''}
                                        onChange={(e) => setNewTenant({ ...newTenant, max_employees: e.target.value ? parseInt(e.target.value) : undefined })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                        placeholder="Unlimited"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Max Users</label>
                                    <input
                                        type="number"
                                        value={newTenant.max_users || 5}
                                        onChange={(e) => setNewTenant({ ...newTenant, max_users: parseInt(e.target.value) || 5 })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                        min="1"
                                    />
                                </div>
                            </div>
                            <div className="mt-6 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={creating}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {creating ? 'Creating...' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Tenants;
