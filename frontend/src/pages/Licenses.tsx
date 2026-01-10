import { useEffect, useState } from 'react';
import { licenseApi, tenantApi } from '../services/api';
import { License, LicenseCreate, Tenant, EmbeddedKeys } from '../types/api';

const Licenses = () => {
    const [licenses, setLicenses] = useState<License[]>([]);
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [showEmbeddedKeys, setShowEmbeddedKeys] = useState(false);
    const [newLicense, setNewLicense] = useState<LicenseCreate>({
        tenant_id: '',
        expiration_days: 365,
        max_employees: undefined,
        max_users: 5,
        features: [],
        embedded_keys: undefined,
    });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [licensesData, tenantsData] = await Promise.all([
                licenseApi.list(),
                tenantApi.list(),
            ]);
            setLicenses(licensesData);
            setTenants(tenantsData);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch data:', err);
            setError('Failed to load licenses');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateLicense = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setCreating(true);
            // Clean up embedded_keys before sending (remove empty values)
            const licenseData = { ...newLicense };
            if (licenseData.embedded_keys) {
                const keys = licenseData.embedded_keys;
                // Remove empty LLM keys
                if (keys.llm_api_keys) {
                    const llm = keys.llm_api_keys;
                    if (!llm.openai && !llm.anthropic && !llm.google) {
                        delete keys.llm_api_keys;
                    }
                }
                // Remove embedded_keys entirely if empty
                if (!keys.admin_api_key && !keys.llm_api_keys) {
                    delete licenseData.embedded_keys;
                }
            }
            await licenseApi.create(licenseData);
            setShowCreateModal(false);
            setShowEmbeddedKeys(false);
            setNewLicense({
                tenant_id: '',
                expiration_days: 365,
                max_employees: undefined,
                max_users: 5,
                features: [],
                embedded_keys: undefined,
            });
            await fetchData();
        } catch (err) {
            console.error('Failed to create license:', err);
            setError('Failed to create license');
        } finally {
            setCreating(false);
        }
    };

    // Helper to update embedded keys
    const updateEmbeddedKeys = (updates: Partial<EmbeddedKeys>) => {
        setNewLicense(prev => ({
            ...prev,
            embedded_keys: {
                ...prev.embedded_keys,
                ...updates,
            }
        }));
    };

    const updateLLMKeys = (provider: 'openai' | 'anthropic' | 'google', value: string) => {
        setNewLicense(prev => ({
            ...prev,
            embedded_keys: {
                ...prev.embedded_keys,
                llm_api_keys: {
                    ...prev.embedded_keys?.llm_api_keys,
                    [provider]: value || undefined,
                }
            }
        }));
    };

    const handleRevokeLicense = async (licenseId: string) => {
        if (!confirm('Are you sure you want to revoke this license?')) return;
        try {
            await licenseApi.revoke(licenseId);
            await fetchData();
        } catch (err) {
            console.error('Failed to revoke license:', err);
            setError('Failed to revoke license');
        }
    };

    const getTenantName = (tenantId: string) => {
        const tenant = tenants.find(t => t.id === tenantId);
        return tenant?.name || 'Unknown';
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    const isExpiringSoon = (expiresAt: string) => {
        const expiry = new Date(expiresAt);
        const now = new Date();
        const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
        return daysUntilExpiry <= 30 && daysUntilExpiry > 0;
    };

    const isExpired = (expiresAt: string) => {
        return new Date(expiresAt) < new Date();
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Licenses</h1>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    + Issue License
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
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tenant</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issued</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
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
                        ) : licenses.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                    No licenses found. Issue your first license to get started.
                                </td>
                            </tr>
                        ) : (
                            licenses.map((license) => (
                                <tr key={license.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="font-medium text-gray-900">{getTenantName(license.tenant_id)}</div>
                                        <div className="text-xs text-gray-500 truncate max-w-xs" title={license.key_string}>
                                            {license.key_string.substring(0, 30)}...
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {formatDate(license.issued_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {formatDate(license.expires_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {license.revoked ? (
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                                Revoked
                                            </span>
                                        ) : isExpired(license.expires_at) ? (
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                                Expired
                                            </span>
                                        ) : isExpiringSoon(license.expires_at) ? (
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                                Expiring Soon
                                            </span>
                                        ) : (
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                                Active
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        {!license.revoked && !isExpired(license.expires_at) && (
                                            <button
                                                onClick={() => handleRevokeLicense(license.id)}
                                                className="text-red-600 hover:text-red-900"
                                            >
                                                Revoke
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create License Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Issue New License</h2>
                        <form onSubmit={handleCreateLicense}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Tenant</label>
                                    <select
                                        required
                                        value={newLicense.tenant_id}
                                        onChange={(e) => setNewLicense({ ...newLicense, tenant_id: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    >
                                        <option value="">Select a tenant</option>
                                        {tenants.map(tenant => (
                                            <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Duration (days)</label>
                                    <input
                                        type="number"
                                        required
                                        min={1}
                                        value={newLicense.expiration_days}
                                        onChange={(e) => setNewLicense({ ...newLicense, expiration_days: parseInt(e.target.value) })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Max Users</label>
                                    <input
                                        type="number"
                                        min={1}
                                        value={newLicense.max_users || ''}
                                        onChange={(e) => setNewLicense({ ...newLicense, max_users: parseInt(e.target.value) || undefined })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Max Employees (optional)</label>
                                    <input
                                        type="number"
                                        min={1}
                                        value={newLicense.max_employees || ''}
                                        onChange={(e) => setNewLicense({ ...newLicense, max_employees: parseInt(e.target.value) || undefined })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Features (comma-separated)</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., analytics, exports, api"
                                        value={newLicense.features?.join(', ') || ''}
                                        onChange={(e) => setNewLicense({
                                            ...newLicense,
                                            features: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                                        })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>

                                {/* Embedded Keys Section */}
                                <div className="border-t pt-4 mt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowEmbeddedKeys(!showEmbeddedKeys)}
                                        className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
                                    >
                                        <span className={`transform transition-transform ${showEmbeddedKeys ? 'rotate-90' : ''}`}>
                                            ▶
                                        </span>
                                        <span className="ml-2">Embedded API Keys (Optional)</span>
                                    </button>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Keys embedded in the license JWT for customer use
                                    </p>

                                    {showEmbeddedKeys && (
                                        <div className="mt-3 space-y-3 pl-4 border-l-2 border-gray-200">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700">
                                                    Admin Panel API Key
                                                </label>
                                                <input
                                                    type="password"
                                                    placeholder="Tenant's API key for admin panel auth"
                                                    value={newLicense.embedded_keys?.admin_api_key || ''}
                                                    onChange={(e) => updateEmbeddedKeys({ admin_api_key: e.target.value || undefined })}
                                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2 text-sm"
                                                />
                                            </div>

                                            <div className="pt-2">
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    LLM Provider Keys
                                                </label>
                                                <div className="space-y-2">
                                                    <div>
                                                        <label className="block text-xs text-gray-500">OpenAI</label>
                                                        <input
                                                            type="password"
                                                            placeholder="sk-..."
                                                            value={newLicense.embedded_keys?.llm_api_keys?.openai || ''}
                                                            onChange={(e) => updateLLMKeys('openai', e.target.value)}
                                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs text-gray-500">Anthropic</label>
                                                        <input
                                                            type="password"
                                                            placeholder="sk-ant-..."
                                                            value={newLicense.embedded_keys?.llm_api_keys?.anthropic || ''}
                                                            onChange={(e) => updateLLMKeys('anthropic', e.target.value)}
                                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs text-gray-500">Google AI</label>
                                                        <input
                                                            type="password"
                                                            placeholder="AIza..."
                                                            value={newLicense.embedded_keys?.llm_api_keys?.google || ''}
                                                            onChange={(e) => updateLLMKeys('google', e.target.value)}
                                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
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
                                    {creating ? 'Issuing...' : 'Issue License'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Licenses;
