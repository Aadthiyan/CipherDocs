import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import {
    Cog6ToothIcon,
    DocumentTextIcon,
    MagnifyingGlassIcon,
    ChartBarIcon,
    ShieldCheckIcon,
    ArrowRightIcon,
    CheckCircleIcon,
    XCircleIcon,
    ClockIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
    const [backendStatus, setBackendStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const { logout, user } = useAuth();

    useEffect(() => {
        const checkBackend = async () => {
            try {
                const response = await api.get('/health');
                setBackendStatus(response.data);
            } catch (error) {
                console.error('Backend health check failed:', error);
                setBackendStatus({ status: 'error', message: error.message });
            } finally {
                setLoading(false);
            }
        };

        checkBackend();
    }, []);

    const quickActions = [
        {
            title: 'Upload Documents',
            description: 'Securely upload and encrypt your documents',
            icon: DocumentTextIcon,
            link: '/documents',
            color: 'from-blue-500 to-cyan-500',
            stats: 'Manage your encrypted knowledge base'
        },
        {
            title: 'Search Documents',
            description: 'AI-powered semantic search across your files',
            icon: MagnifyingGlassIcon,
            link: '/search',
            color: 'from-purple-500 to-pink-500',
            stats: 'Query your database securely'
        },
        {
            title: 'View Analytics',
            description: 'Monitor usage and performance metrics',
            icon: ChartBarIcon,
            link: '/analytics',
            color: 'from-green-500 to-emerald-500',
            stats: 'Track performance insights'
        }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a]">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            <div className="fixed bottom-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />

            {/* Navigation */}
            <nav className="relative z-50 glass-strong border-b border-gray-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-20">
                        <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center glow">
                                <ShieldCheckIcon className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold gradient-text">CyborgDB</h1>
                                <p className="text-xs text-gray-400">Dashboard</p>
                            </div>
                        </div>

                        {/* Navigation Links */}
                        <div className="hidden md:flex items-center space-x-6">
                            <Link to="/dashboard" className="text-indigo-400 font-semibold">Dashboard</Link>
                            <Link to="/documents" className="text-gray-400 hover:text-white transition-colors">Documents</Link>
                            <Link to="/search" className="text-gray-400 hover:text-white transition-colors">Search</Link>
                            <Link to="/analytics" className="text-gray-400 hover:text-white transition-colors">Analytics</Link>
                        </div>

                        <div className="flex items-center space-x-4">
                            <Link
                                to="/settings"
                                className="p-2 text-gray-400 hover:text-indigo-400 transition-colors rounded-lg hover:bg-white/5"
                                title="Settings"
                            >
                                <Cog6ToothIcon className="h-6 w-6" />
                            </Link>
                            <button
                                onClick={logout}
                                className="px-4 py-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg hover:bg-red-500/20 transition-all font-semibold"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="relative max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Welcome Section */}
                <div className="mb-8 fade-in">
                    <h2 className="text-4xl font-black text-white mb-2">
                        Welcome Back{user?.email ? `, ${user.email.split('@')[0]}` : ''}! 👋
                    </h2>
                    <p className="text-xl text-gray-400">
                        Your secure workspace is ready. What would you like to do today?
                    </p>
                </div>

                {/* System Status Card */}
                <div className="mb-8 slide-in-left">
                    <div className="card p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                                    {loading ? (
                                        <ClockIcon className="w-7 h-7 text-white animate-spin" />
                                    ) : backendStatus?.status === 'healthy' ? (
                                        <CheckCircleIcon className="w-7 h-7 text-white" />
                                    ) : (
                                        <XCircleIcon className="w-7 h-7 text-white" />
                                    )}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">System Status</h3>
                                    <p className="text-gray-400">
                                        {loading ? 'Checking system health...' : 'All systems operational'}
                                    </p>
                                </div>
                            </div>
                            <div>
                                {!loading && (
                                    <span className={`px-4 py-2 rounded-lg font-bold text-sm ${backendStatus?.status === 'healthy'
                                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                                        }`}>
                                        {backendStatus?.status === 'healthy' ? '✓ Healthy' : '✗ Error'}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Quick Actions Grid */}
                <div className="mb-8">
                    <h3 className="text-2xl font-bold text-white mb-6">Quick Actions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {quickActions.map((action, index) => (
                            <Link
                                key={index}
                                to={action.link}
                                className="card scale-hover glow-hover fade-in"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className={`w-14 h-14 bg-gradient-to-br ${action.color} rounded-xl flex items-center justify-center mb-6 glow`}>
                                    <action.icon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">{action.title}</h3>
                                <p className="text-gray-400 mb-4">{action.description}</p>
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-gray-500">{action.stats}</span>
                                    <ArrowRightIcon className="w-5 h-5 text-indigo-400 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Security Features */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div className="card slide-in-left">
                        <div className="flex items-start space-x-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
                                <ShieldCheckIcon className="w-7 h-7 text-white" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white mb-2">End-to-End Encryption</h3>
                                <p className="text-gray-400 mb-4">
                                    All your documents are encrypted with AES-256 encryption. Your data remains secure at rest, in transit, and during search operations.
                                </p>
                                <div className="flex items-center space-x-2 text-sm text-green-400">
                                    <CheckCircleIcon className="w-5 h-5" />
                                    <span>Active & Protected</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card slide-in-right">
                        <div className="flex items-start space-x-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
                                <ChartBarIcon className="w-7 h-7 text-white" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white mb-2">Multi-Tenant Isolation</h3>
                                <p className="text-gray-400 mb-4">
                                    Your tenant data is cryptographically isolated from all other tenants. Zero cross-tenant data leakage guaranteed.
                                </p>
                                <div className="flex items-center space-x-2 text-sm text-green-400">
                                    <CheckCircleIcon className="w-5 h-5" />
                                    <span>100% Isolated</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Getting Started Guide */}
                <div className="card p-8 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20 fade-in">
                    <h3 className="text-2xl font-bold text-white mb-4">Getting Started</h3>
                    <p className="text-gray-300 mb-6">
                        Follow these steps to make the most of your CyborgDB workspace:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold">1</div>
                            <div>
                                <h4 className="font-bold text-white mb-1">Upload Documents</h4>
                                <p className="text-sm text-gray-400">Add your first documents to build your knowledge base</p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold">2</div>
                            <div>
                                <h4 className="font-bold text-white mb-1">Search & Discover</h4>
                                <p className="text-sm text-gray-400">Use AI-powered search to find relevant information</p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-cyan-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold">3</div>
                            <div>
                                <h4 className="font-bold text-white mb-1">Monitor Analytics</h4>
                                <p className="text-sm text-gray-400">Track usage patterns and performance metrics</p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;
