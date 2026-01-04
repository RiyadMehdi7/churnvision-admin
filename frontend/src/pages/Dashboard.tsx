import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '../services/api';
import { DashboardStats } from '../types/api';

const StatCard = ({ title, value, subtext, loading }: { title: string; value: string; subtext: string; loading?: boolean }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
        {loading ? (
            <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-20 mt-2"></div>
                <div className="h-4 bg-gray-200 rounded w-32 mt-2"></div>
            </div>
        ) : (
            <>
                <div className="text-3xl font-bold mt-2">{value}</div>
                <div className="text-green-500 text-sm mt-1">{subtext}</div>
            </>
        )}
    </div>
);

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoading(true);
                const data = await dashboardApi.getStats();
                setStats(data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch dashboard stats:', err);
                setError('Failed to load dashboard data');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    const formatMRR = (mrr: number) => {
        if (mrr >= 1000000) {
            return `$${(mrr / 1000000).toFixed(1)}M`;
        }
        if (mrr >= 1000) {
            return `$${(mrr / 1000).toFixed(0)}K`;
        }
        return `$${mrr.toFixed(0)}`;
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-800">Overview</h1>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard
                    title="Total Tenants"
                    value={stats?.total_tenants?.toString() || '0'}
                    subtext={`${stats?.trial_tenants || 0} in trial`}
                    loading={loading}
                />
                <StatCard
                    title="MRR"
                    value={formatMRR(stats?.mrr || 0)}
                    subtext={`${stats?.active_tenants || 0} active subscriptions`}
                    loading={loading}
                />
                <StatCard
                    title="Latest Version"
                    value={stats?.latest_version || 'N/A'}
                    subtext={`${stats?.tenants_on_latest || 0} tenants on latest`}
                    loading={loading}
                />
                <StatCard
                    title="System Health"
                    value={stats?.overdue_invoices_count === 0 ? '100%' : 'Attention'}
                    subtext={stats?.overdue_invoices_count === 0 ? 'All systems operational' : `${stats?.overdue_invoices_count} issues`}
                    loading={loading}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow-sm">
                    <h2 className="text-lg font-bold mb-4">Action Required</h2>
                    {loading ? (
                        <div className="animate-pulse space-y-3">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-8 bg-gray-200 rounded"></div>
                            ))}
                        </div>
                    ) : (
                        <ul className="space-y-3">
                            {(stats?.expiring_licenses_count || 0) > 0 && (
                                <li className="flex justify-between items-center text-sm border-b pb-2">
                                    <span>&#9888; {stats?.expiring_licenses_count} licenses expiring in 30 days</span>
                                    <button
                                        onClick={() => navigate('/licenses')}
                                        className="text-blue-500 hover:underline"
                                    >
                                        View
                                    </button>
                                </li>
                            )}
                            {(stats?.overdue_invoices_count || 0) > 0 && (
                                <li className="flex justify-between items-center text-sm border-b pb-2">
                                    <span className="text-red-600">&#128308; {stats?.overdue_invoices_count} invoices overdue</span>
                                    <button
                                        onClick={() => navigate('/billing')}
                                        className="text-blue-500 hover:underline"
                                    >
                                        View
                                    </button>
                                </li>
                            )}
                            {(stats?.deprecated_version_tenants || 0) > 0 && (
                                <li className="flex justify-between items-center text-sm border-b pb-2">
                                    <span>&#9888; {stats?.deprecated_version_tenants} tenants on deprecated version</span>
                                    <button
                                        onClick={() => navigate('/tenants')}
                                        className="text-blue-500 hover:underline"
                                    >
                                        View
                                    </button>
                                </li>
                            )}
                            {(stats?.expiring_licenses_count || 0) === 0 &&
                             (stats?.overdue_invoices_count || 0) === 0 &&
                             (stats?.deprecated_version_tenants || 0) === 0 && (
                                <li className="text-sm text-gray-500 py-2">
                                    No action items at this time
                                </li>
                            )}
                        </ul>
                    )}
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                    <h2 className="text-lg font-bold mb-4">Quick Stats</h2>
                    {loading ? (
                        <div className="animate-pulse space-y-3">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-8 bg-gray-200 rounded"></div>
                            ))}
                        </div>
                    ) : (
                        <ul className="space-y-3">
                            <li className="flex justify-between items-center text-sm border-b pb-2">
                                <span>Active Tenants</span>
                                <span className="font-medium">{stats?.active_tenants || 0}</span>
                            </li>
                            <li className="flex justify-between items-center text-sm border-b pb-2">
                                <span>Trial Tenants</span>
                                <span className="font-medium">{stats?.trial_tenants || 0}</span>
                            </li>
                            <li className="flex justify-between items-center text-sm border-b pb-2">
                                <span>Tenants on Latest Version</span>
                                <span className="font-medium">{stats?.tenants_on_latest || 0}</span>
                            </li>
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
