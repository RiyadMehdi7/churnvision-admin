import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { LayoutDashboard, Users, Zap, Terminal, CreditCard, LifeBuoy } from 'lucide-react';

const Sidebar = () => (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4">
        <div className="text-2xl font-bold mb-8 text-blue-400">ChurnVision</div>
        <nav className="space-y-4">
            <Link to="/" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <LayoutDashboard size={20} /> <span>Dashboard</span>
            </Link>
            <Link to="/tenants" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <Users size={20} /> <span>Tenants</span>
            </Link>
            <Link to="/licenses" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <Zap size={20} /> <span>Licenses</span>
            </Link>
            <Link to="/releases" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <Terminal size={20} /> <span>Releases</span>
            </Link>
            <Link to="/billing" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <CreditCard size={20} /> <span>Billing</span>
            </Link>
            <Link to="/support" className="flex items-center space-x-2 p-2 hover:bg-gray-800 rounded">
                <LifeBuoy size={20} /> <span>Support</span>
            </Link>
        </nav>
    </div>
);

const Layout = () => {
    return (
        <div className="flex bg-gray-100 min-h-screen">
            <Sidebar />
            <div className="flex-1 p-8">
                <Outlet />
            </div>
        </div>
    );
};

export default Layout;
