import React, { useState, useEffect } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';
import {
    ChartBarIcon,
    ClockIcon,
    MagnifyingGlassIcon,
    ExclamationTriangleIcon,
    ArrowLeftIcon,
    CheckCircleIcon,
    BoltIcon
} from '@heroicons/react/24/outline';

const Analytics = () => {
    const [searchStats, setSearchStats] = useState(null);
    const [popularQueries, setPopularQueries] = useState([]);
    const [noResults, setNoResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, popularRes, noResRes] = await Promise.all([
                    api.get('/api/v1/analytics/search'),
                    api.get('/api/v1/analytics/popular-queries?limit=10'),
                    api.get('/api/v1/analytics/no-results?limit=5')
                ]);

                setSearchStats(statsRes.data);
                setPopularQueries(popularRes.data);
                setNoResults(noResRes.data);
            } catch (error) {
                console.error("Failed to fetch analytics", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a] flex items-center justify-center">
            <div className="text-center">
                <div className="spinner mb-4 mx-auto"></div>
                <p className="text-gray-400">Loading analytics...</p>
            </div>
        </div>
    );

    const queryData = popularQueries.map(q => ({
        name: q.query_text.length > 20 ? q.query_text.substring(0, 20) + '...' : q.query_text,
        count: q.count,
        full: q.query_text
    }));

    const kpiCards = [
        {
            title: 'Total Searches',
            value: searchStats?.total_searches || 0,
            icon: MagnifyingGlassIcon,
            color: 'from-blue-500 to-cyan-500',
            suffix: ''
        },
        {
            title: 'Avg Latency',
            value: searchStats?.avg_latency_ms?.toFixed(0) || 0,
            icon: BoltIcon,
            color: 'from-indigo-500 to-purple-500',
            suffix: 'ms'
        },
        {
            title: 'P95 Latency',
            value: searchStats?.p95_latency_ms?.toFixed(0) || 0,
            icon: ClockIcon,
            color: 'from-purple-500 to-pink-500',
            suffix: 'ms'
        },
        {
            title: 'Empty Results',
            value: ((searchStats?.zero_result_rate || 0) * 100).toFixed(1),
            icon: ((searchStats?.zero_result_rate || 0) > 0.1) ? ExclamationTriangleIcon : CheckCircleIcon,
            color: ((searchStats?.zero_result_rate || 0) > 0.1) ? 'from-red-500 to-orange-500' : 'from-green-500 to-emerald-500',
            suffix: '%'
        }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a]">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 left-0 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
            <div className="fixed bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />

            {/* Content */}
            <div className="relative max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8 fade-in">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-4"
                    >
                        <ArrowLeftIcon className="w-5 h-5" />
                        <span>Back to Dashboard</span>
                    </button>

                    <h2 className="text-4xl font-black text-white mb-2">
                        Search Analytics
                    </h2>
                    <p className="text-xl text-gray-400">
                        Insights into user search behavior and system performance
                    </p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {kpiCards.map((kpi, index) => (
                        <div
                            key={index}
                            className="card scale-hover fade-in"
                            style={{ animationDelay: `${index * 100}ms` }}
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className={`w-12 h-12 bg-gradient-to-br ${kpi.color} rounded-xl flex items-center justify-center glow`}>
                                    <kpi.icon className="w-7 h-7 text-white" />
                                </div>
                            </div>
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                                {kpi.title}
                            </h3>
                            <div className="flex items-baseline">
                                <p className="text-4xl font-black text-white">
                                    {kpi.value}
                                </p>
                                {kpi.suffix && (
                                    <span className="ml-2 text-lg text-gray-500 font-semibold">
                                        {kpi.suffix}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Charts Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Popular Queries Chart */}
                    <div className="glass-strong rounded-2xl p-8 slide-in-left">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                                <ChartBarIcon className="w-6 h-6 text-white" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">Top Search Terms</h3>
                        </div>

                        {queryData.length > 0 ? (
                            <div className="h-96">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart
                                        data={queryData}
                                        layout="vertical"
                                        margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
                                    >
                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                            horizontal={false}
                                            stroke="rgba(255, 255, 255, 0.1)"
                                        />
                                        <XAxis
                                            type="number"
                                            hide
                                        />
                                        <YAxis
                                            dataKey="name"
                                            type="category"
                                            width={140}
                                            tick={{ fontSize: 12, fill: '#9ca3af' }}
                                            axisLine={false}
                                            tickLine={false}
                                        />
                                        <Tooltip
                                            cursor={{ fill: 'rgba(99, 102, 241, 0.1)' }}
                                            contentStyle={{
                                                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                                                border: '1px solid rgba(99, 102, 241, 0.3)',
                                                borderRadius: '0.75rem',
                                                padding: '12px',
                                                backdropFilter: 'blur(12px)'
                                            }}
                                            labelStyle={{ color: '#f9fafb', fontWeight: 'bold' }}
                                            itemStyle={{ color: '#818cf8' }}
                                        />
                                        <Bar
                                            dataKey="count"
                                            fill="url(#colorGradient)"
                                            radius={[0, 8, 8, 0]}
                                            barSize={24}
                                        />
                                        <defs>
                                            <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                                                <stop offset="0%" stopColor="#6366f1" />
                                                <stop offset="100%" stopColor="#8b5cf6" />
                                            </linearGradient>
                                        </defs>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="h-96 flex items-center justify-center bg-gray-800/30 rounded-xl border-2 border-dashed border-gray-700">
                                <div className="text-center">
                                    <MagnifyingGlassIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                                    <p className="text-gray-400">No search data available yet</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Content Gaps */}
                    <div className="glass-strong rounded-2xl p-8 slide-in-right">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                                <ExclamationTriangleIcon className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">Content Gaps</h3>
                                <p className="text-sm text-gray-400">Queries with zero results</p>
                            </div>
                        </div>

                        <div className="overflow-hidden rounded-xl border border-gray-700">
                            <table className="min-w-full divide-y divide-gray-700">
                                <thead className="bg-gray-800/50">
                                    <tr>
                                        <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            Query Term
                                        </th>
                                        <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            Attempts
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {noResults.length > 0 ? (
                                        noResults.map((item, i) => (
                                            <tr key={i} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4 text-sm font-medium text-gray-200 max-w-xs truncate" title={item.query_text}>
                                                    {item.query_text}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-400 text-right font-mono font-bold">
                                                    {item.count}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="2" className="px-6 py-16 text-center">
                                                <div className="flex flex-col items-center">
                                                    <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mb-4">
                                                        <CheckCircleIcon className="w-10 h-10 text-green-400" />
                                                    </div>
                                                    <p className="text-lg font-semibold text-white mb-1">All Clear!</p>
                                                    <p className="text-sm text-gray-400">All queries are finding results</p>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {noResults.length > 0 && (
                            <div className="mt-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                                <p className="text-sm text-orange-200">
                                    <strong>Tip:</strong> Consider uploading content covering these topics to improve search results.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Performance Insights */}
                <div className="mt-8 card bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20 p-8 fade-in">
                    <h3 className="text-2xl font-bold text-white mb-4">Performance Insights</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-white text-sm">
                                ✓
                            </div>
                            <div>
                                <h4 className="font-bold text-white mb-1">Fast Response Times</h4>
                                <p className="text-sm text-gray-400">
                                    Average latency of {searchStats?.avg_latency_ms?.toFixed(0) || 0}ms ensures quick search results
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-white text-sm">
                                ✓
                            </div>
                            <div>
                                <h4 className="font-bold text-white mb-1">Encrypted Search</h4>
                                <p className="text-sm text-gray-400">
                                    All searches are performed on encrypted embeddings for maximum security
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-cyan-500 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-white text-sm">
                                ✓
                            </div>
                            <div>
                                <h4 className="font-bold text-white mb-1">AI-Powered Results</h4>
                                <p className="text-sm text-gray-400">
                                    Semantic search delivers relevant results beyond keyword matching
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
