import { useEffect, useState } from 'react';
import { releaseApi } from '../services/api';
import { Release, ReleaseCreate, ReleaseTrack, ReleaseStatus } from '../types/api';

const trackColors: Record<ReleaseTrack, string> = {
    [ReleaseTrack.STABLE]: 'bg-green-100 text-green-800',
    [ReleaseTrack.BETA]: 'bg-yellow-100 text-yellow-800',
    [ReleaseTrack.LTS]: 'bg-blue-100 text-blue-800',
};

const statusColors: Record<ReleaseStatus, string> = {
    [ReleaseStatus.PUBLISHED]: 'text-green-600',
    [ReleaseStatus.DRAFT]: 'text-gray-600',
    [ReleaseStatus.DEPRECATED]: 'text-red-600',
};

const Releases = () => {
    const [releases, setReleases] = useState<Release[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newRelease, setNewRelease] = useState<ReleaseCreate>({
        version: '',
        track: ReleaseTrack.STABLE,
        status: ReleaseStatus.DRAFT,
        docker_images: [],
        requires_downtime: false,
        breaking_changes: [],
        release_notes: '',
    });

    const fetchReleases = async () => {
        try {
            setLoading(true);
            const data = await releaseApi.list();
            setReleases(data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch releases:', err);
            setError('Failed to load releases');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReleases();
    }, []);

    const handleCreateRelease = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setCreating(true);
            await releaseApi.create(newRelease);
            setShowCreateModal(false);
            setNewRelease({
                version: '',
                track: ReleaseTrack.STABLE,
                status: ReleaseStatus.DRAFT,
                docker_images: [],
                requires_downtime: false,
                breaking_changes: [],
                release_notes: '',
            });
            await fetchReleases();
        } catch (err) {
            console.error('Failed to create release:', err);
            setError('Failed to create release');
        } finally {
            setCreating(false);
        }
    };

    const handlePublish = async (version: string) => {
        try {
            await releaseApi.update(version, { status: ReleaseStatus.PUBLISHED });
            await fetchReleases();
        } catch (err) {
            console.error('Failed to publish release:', err);
            setError('Failed to publish release');
        }
    };

    const handleDeprecate = async (version: string) => {
        if (!confirm('Are you sure you want to deprecate this release?')) return;
        try {
            await releaseApi.update(version, { status: ReleaseStatus.DEPRECATED });
            await fetchReleases();
        } catch (err) {
            console.error('Failed to deprecate release:', err);
            setError('Failed to deprecate release');
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Releases</h1>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    + Draft Release
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                    <button onClick={() => setError(null)} className="float-right">&times;</button>
                </div>
            )}

            <div className="space-y-4">
                {loading ? (
                    <div className="animate-pulse space-y-4">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="bg-white p-4 rounded shadow h-20"></div>
                        ))}
                    </div>
                ) : releases.length === 0 ? (
                    <div className="bg-white p-8 rounded shadow text-center text-gray-500">
                        No releases found. Create your first release to get started.
                    </div>
                ) : (
                    releases.map((release) => (
                        <div key={release.id} className="bg-white p-4 rounded shadow flex justify-between items-center">
                            <div>
                                <div className="flex items-center space-x-3">
                                    <span className="text-lg font-bold">{release.version}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs ${trackColors[release.track]}`}>
                                        {release.track}
                                    </span>
                                    {release.requires_downtime && (
                                        <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-800">
                                            Requires Downtime
                                        </span>
                                    )}
                                </div>
                                <div className="text-sm text-gray-500 mt-1">
                                    {release.published_at
                                        ? `Published: ${formatDate(release.published_at)}`
                                        : `Created: ${formatDate(release.created_at)}`
                                    }
                                </div>
                                {release.release_notes && (
                                    <div className="text-sm text-gray-600 mt-2 max-w-xl truncate">
                                        {release.release_notes}
                                    </div>
                                )}
                            </div>
                            <div className="flex items-center space-x-4">
                                <span className={`font-medium ${statusColors[release.status]}`}>
                                    {release.status}
                                </span>
                                <div className="space-x-2">
                                    {release.status === ReleaseStatus.DRAFT && (
                                        <button
                                            onClick={() => handlePublish(release.version)}
                                            className="text-green-600 hover:underline"
                                        >
                                            Publish
                                        </button>
                                    )}
                                    {release.status === ReleaseStatus.PUBLISHED && (
                                        <button
                                            onClick={() => handleDeprecate(release.version)}
                                            className="text-red-600 hover:underline"
                                        >
                                            Deprecate
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Release Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
                        <h2 className="text-xl font-bold mb-4">Draft New Release</h2>
                        <form onSubmit={handleCreateRelease}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Version</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="e.g., 2.1.0 or 2.2.0-beta.1"
                                        value={newRelease.version}
                                        onChange={(e) => setNewRelease({ ...newRelease, version: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Track</label>
                                    <select
                                        value={newRelease.track}
                                        onChange={(e) => setNewRelease({ ...newRelease, track: e.target.value as ReleaseTrack })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    >
                                        <option value={ReleaseTrack.STABLE}>Stable</option>
                                        <option value={ReleaseTrack.BETA}>Beta</option>
                                        <option value={ReleaseTrack.LTS}>LTS</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Docker Images (comma-separated)</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., churnvision/api:2.1.0, churnvision/worker:2.1.0"
                                        value={newRelease.docker_images?.join(', ') || ''}
                                        onChange={(e) => setNewRelease({
                                            ...newRelease,
                                            docker_images: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                                        })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={newRelease.requires_downtime}
                                            onChange={(e) => setNewRelease({ ...newRelease, requires_downtime: e.target.checked })}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="ml-2 text-sm text-gray-700">Requires Downtime</span>
                                    </label>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Release Notes</label>
                                    <textarea
                                        rows={4}
                                        value={newRelease.release_notes || ''}
                                        onChange={(e) => setNewRelease({ ...newRelease, release_notes: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border px-3 py-2"
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
                                    {creating ? 'Creating...' : 'Create Draft'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Releases;
