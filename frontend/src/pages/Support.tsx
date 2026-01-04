import { useEffect, useState } from 'react';
import { supportApi, tenantApi } from '../services/api';
import { Ticket, TicketCreate, Announcement, AnnouncementCreate, Tenant } from '../types/api';

const priorityColors: Record<string, string> = {
    'LOW': 'bg-gray-100 text-gray-800',
    'NORMAL': 'bg-blue-100 text-blue-800',
    'HIGH': 'bg-orange-100 text-orange-800',
    'URGENT': 'bg-red-100 text-red-800',
};

const statusColors: Record<string, string> = {
    'OPEN': 'bg-yellow-100 text-yellow-800',
    'IN_PROGRESS': 'bg-blue-100 text-blue-800',
    'RESOLVED': 'bg-green-100 text-green-800',
    'CLOSED': 'bg-gray-100 text-gray-800',
};

const Support = () => {
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'tickets' | 'announcements'>('tickets');
    const [showTicketModal, setShowTicketModal] = useState(false);
    const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newTicket, setNewTicket] = useState<TicketCreate>({
        tenant_id: '',
        subject: '',
        description: '',
        priority: 'NORMAL',
    });
    const [newAnnouncement, setNewAnnouncement] = useState<AnnouncementCreate>({
        title: '',
        content: '',
    });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [ticketsData, announcementsData, tenantsData] = await Promise.all([
                supportApi.listTickets(),
                supportApi.listAnnouncements(),
                tenantApi.list(),
            ]);
            setTickets(ticketsData);
            setAnnouncements(announcementsData);
            setTenants(tenantsData);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch support data:', err);
            setError('Failed to load support data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateTicket = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setCreating(true);
            await supportApi.createTicket(newTicket);
            setShowTicketModal(false);
            setNewTicket({ tenant_id: '', subject: '', description: '', priority: 'NORMAL' });
            await fetchData();
        } catch (err) {
            console.error('Failed to create ticket:', err);
            setError('Failed to create ticket');
        } finally {
            setCreating(false);
        }
    };

    const handleCreateAnnouncement = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setCreating(true);
            await supportApi.createAnnouncement(newAnnouncement);
            setShowAnnouncementModal(false);
            setNewAnnouncement({ title: '', content: '' });
            await fetchData();
        } catch (err) {
            console.error('Failed to create announcement:', err);
            setError('Failed to create announcement');
        } finally {
            setCreating(false);
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
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Support</h1>
                <div className="space-x-2">
                    {activeTab === 'tickets' && (
                        <button
                            onClick={() => setShowTicketModal(true)}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                        >
                            + New Ticket
                        </button>
                    )}
                    {activeTab === 'announcements' && (
                        <button
                            onClick={() => setShowAnnouncementModal(true)}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                        >
                            + New Announcement
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                    <button onClick={() => setError(null)} className="float-right">&times;</button>
                </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setActiveTab('tickets')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'tickets'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Tickets
                    </button>
                    <button
                        onClick={() => setActiveTab('announcements')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'announcements'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Announcements
                    </button>
                </nav>
            </div>

            {activeTab === 'tickets' && (
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tenant</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
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
                            ) : tickets.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                        No tickets found.
                                    </td>
                                </tr>
                            ) : (
                                tickets.map((ticket) => (
                                    <tr key={ticket.id}>
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-gray-900">{ticket.subject}</div>
                                            <div className="text-sm text-gray-500 truncate max-w-md">{ticket.description}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {getTenantName(ticket.tenant_id)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${priorityColors[ticket.priority] || 'bg-gray-100 text-gray-800'}`}>
                                                {ticket.priority}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[ticket.status] || 'bg-gray-100 text-gray-800'}`}>
                                                {ticket.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(ticket.created_at)}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {activeTab === 'announcements' && (
                <div className="space-y-4">
                    {loading ? (
                        <div className="animate-pulse space-y-4">
                            {[1, 2].map(i => (
                                <div key={i} className="bg-white p-4 rounded shadow h-24"></div>
                            ))}
                        </div>
                    ) : announcements.length === 0 ? (
                        <div className="bg-white p-8 rounded shadow text-center text-gray-500">
                            No announcements found.
                        </div>
                    ) : (
                        announcements.map((announcement) => (
                            <div key={announcement.id} className="bg-white p-6 rounded shadow">
                                <div className="flex justify-between items-start">
                                    <h3 className="text-lg font-bold text-gray-900">{announcement.title}</h3>
                                    <span className="text-sm text-gray-500">{formatDate(announcement.published_at)}</span>
                                </div>
                                <p className="mt-2 text-gray-600">{announcement.content}</p>
                                {announcement.expires_at && (
                                    <p className="mt-2 text-sm text-gray-400">Expires: {formatDate(announcement.expires_at)}</p>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Create Ticket Modal */}
            {showTicketModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Create Support Ticket</h2>
                        <form onSubmit={handleCreateTicket}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Tenant</label>
                                    <select
                                        required
                                        value={newTicket.tenant_id}
                                        onChange={(e) => setNewTicket({ ...newTicket, tenant_id: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    >
                                        <option value="">Select a tenant</option>
                                        {tenants.map(tenant => (
                                            <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Subject</label>
                                    <input
                                        type="text"
                                        required
                                        value={newTicket.subject}
                                        onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Priority</label>
                                    <select
                                        value={newTicket.priority}
                                        onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    >
                                        <option value="LOW">Low</option>
                                        <option value="NORMAL">Normal</option>
                                        <option value="HIGH">High</option>
                                        <option value="URGENT">Urgent</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Description</label>
                                    <textarea
                                        required
                                        rows={4}
                                        value={newTicket.description}
                                        onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                            </div>
                            <div className="mt-6 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowTicketModal(false)}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={creating}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {creating ? 'Creating...' : 'Create Ticket'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Create Announcement Modal */}
            {showAnnouncementModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Create Announcement</h2>
                        <form onSubmit={handleCreateAnnouncement}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Title</label>
                                    <input
                                        type="text"
                                        required
                                        value={newAnnouncement.title}
                                        onChange={(e) => setNewAnnouncement({ ...newAnnouncement, title: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Content</label>
                                    <textarea
                                        required
                                        rows={4}
                                        value={newAnnouncement.content}
                                        onChange={(e) => setNewAnnouncement({ ...newAnnouncement, content: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Expires At (optional)</label>
                                    <input
                                        type="datetime-local"
                                        value={newAnnouncement.expires_at || ''}
                                        onChange={(e) => setNewAnnouncement({ ...newAnnouncement, expires_at: e.target.value || undefined })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                            </div>
                            <div className="mt-6 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowAnnouncementModal(false)}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={creating}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {creating ? 'Publishing...' : 'Publish'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Support;
