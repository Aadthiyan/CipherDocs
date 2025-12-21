import React, { useState } from 'react';
import api from '../api/client';
import { toast } from 'react-hot-toast';
import {
    MagnifyingGlassIcon,
    DocumentTextIcon,
    ChartBarIcon,
    ClockIcon,
    SparklesIcon,
    ExclamationCircleIcon,
    ArrowLeftIcon,
    LightBulbIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

const Search = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [metrics, setMetrics] = useState(null);
    const [llmResult, setLlmResult] = useState(null);
    const navigate = useNavigate();

    // Client-side pagination setting
    const [topK] = useState(10);
    const [currentPage, setCurrentPage] = useState(1);
    const resultsPerPage = 5;

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setResults([]);
        setMetrics(null);
        setLlmResult(null);
        setCurrentPage(1);

        try {
            const payload = {
                query: query,
                top_k: topK,
                augment: true,
                rerank: true
            };

            const response = await api.post('/api/v1/search/advanced', payload);
            setResults(response.data.results || []);
            setMetrics({
                latency: response.data.latency_ms,
                total: response.data.total_results,
                query_id: response.data.query_id
            });

            if (response.data.llm_answer) {
                setLlmResult({
                    answer: response.data.llm_answer,
                    sources: response.data.llm_sources || [],
                    confidence: response.data.llm_confidence || 0,
                    disclaimer: response.data.llm_disclaimer
                });
            }
        } catch (error) {
            console.error('Search failed', error);
            toast.error('Search failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Pagination Logic
    const indexOfLastResult = currentPage * resultsPerPage;
    const indexOfFirstResult = indexOfLastResult - resultsPerPage;
    const currentResults = results.slice(indexOfFirstResult, indexOfLastResult);
    const totalPages = Math.ceil(results.length / resultsPerPage);

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a]">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            <div className="fixed bottom-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />

            {/* Content */}
            <div className="relative max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
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
                        Encrypted Search
                    </h2>
                    <p className="text-xl text-gray-400">
                        AI-powered semantic search across your encrypted documents
                    </p>
                </div>

                {/* Search Box */}
                <div className="glass-strong rounded-2xl p-8 mb-8 shadow-2xl slide-in-left">
                    <form onSubmit={handleSearch}>
                        <div className="flex items-center space-x-4">
                            <div className="flex-shrink-0">
                                <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                                    <MagnifyingGlassIcon className="h-6 w-6 text-white" />
                                </div>
                            </div>
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    className="input-modern pr-32 py-4 text-lg w-full"
                                    placeholder="Ask a question about your documents..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    autoFocus
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !query.trim()}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Searching...' : 'Search'}
                                </button>
                            </div>
                        </div>
                    </form>

                    {/* Metrics Display */}
                    {metrics && (
                        <div className="mt-6 flex items-center flex-wrap gap-4 text-sm border-t border-gray-700 pt-4">
                            <div className="flex items-center space-x-2 px-3 py-1.5 bg-indigo-500/20 border border-indigo-500/30 rounded-lg">
                                <ClockIcon className="h-4 w-4 text-indigo-400" />
                                <span className="text-indigo-300 font-semibold">{metrics.latency.toFixed(0)}ms</span>
                            </div>
                            <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-lg">
                                <DocumentTextIcon className="h-4 w-4 text-green-400" />
                                <span className="text-green-300 font-semibold">{metrics.total} results</span>
                            </div>
                            <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-700/50 border border-gray-600 rounded-lg">
                                <span className="text-gray-400 font-mono text-xs">ID: {metrics.query_id.slice(0, 8)}</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Results */}
                <div className="space-y-6">
                    {/* LLM Answer Section */}
                    {llmResult && (
                        <div className="card bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border-indigo-500/30 p-8 slide-in-right">
                            <div className="flex items-start space-x-4 mb-4">
                                <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0 glow">
                                    <SparklesIcon className="w-7 h-7 text-white" />
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-2xl font-bold text-white mb-3">AI-Generated Answer</h3>
                                    <p className="text-lg text-gray-200 leading-relaxed">{llmResult.answer}</p>
                                </div>
                            </div>

                            {/* Confidence */}
                            <div className="flex items-center space-x-3 mt-6 pt-6 border-t border-indigo-500/30">
                                <span className="text-sm font-semibold text-gray-300">Confidence:</span>
                                <div className="flex-1 max-w-xs h-3 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all ${llmResult.confidence > 0.7
                                            ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                                            : llmResult.confidence > 0.5
                                                ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                                                : 'bg-gradient-to-r from-red-500 to-pink-500'
                                            }`}
                                        style={{ width: `${llmResult.confidence * 100}%` }}
                                    />
                                </div>
                                <span className="text-sm font-bold text-white">
                                    {(llmResult.confidence * 100).toFixed(0)}%
                                </span>
                            </div>

                            {/* Disclaimer */}
                            {llmResult.disclaimer && (
                                <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start space-x-3">
                                    <ExclamationCircleIcon className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                                    <p className="text-sm text-yellow-200">{llmResult.disclaimer}</p>
                                </div>
                            )}

                            {/* Sources */}
                            {llmResult.sources && llmResult.sources.length > 0 && (
                                <div className="mt-6">
                                    <p className="text-sm font-semibold text-gray-300 mb-3">Sources:</p>
                                    <div className="grid grid-cols-1 gap-2">
                                        {llmResult.sources.map((source, idx) => (
                                            <div key={idx} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-gray-300">
                                                <span className="font-semibold text-indigo-400">Source {idx + 1}:</span> {source.filename || source.source || 'Unknown'}
                                                {source.page_number && <span className="text-gray-500"> (Page {source.page_number})</span>}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Loading Skeletons */}
                    {loading && (
                        <>
                            {[...Array(3)].map((_, i) => (
                                <div key={i} className="card animate-pulse">
                                    <div className="flex justify-between mb-4">
                                        <div className="h-6 bg-gray-700 rounded w-1/3"></div>
                                        <div className="h-6 bg-gray-700 rounded w-20"></div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="h-4 bg-gray-700 rounded w-full"></div>
                                        <div className="h-4 bg-gray-700 rounded w-full"></div>
                                        <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                                    </div>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Results List */}
                    {!loading && results.length > 0 && (
                        <>
                            {currentResults.map((result, index) => (
                                <div
                                    key={result.id}
                                    className="card hover:border-indigo-500/50 transition-all fade-in"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                                                <DocumentTextIcon className="w-6 h-6 text-white" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-bold text-white">
                                                    {result.metadata?.filename || 'Unknown Document'}
                                                </h3>
                                                <div className="flex items-center space-x-2 text-xs text-gray-500 mt-1">
                                                    <span className="px-2 py-0.5 bg-gray-700 rounded">
                                                        Page {result.metadata?.page_number || result.metadata?.page || '?'}
                                                    </span>
                                                    {result.metadata?.section && (
                                                        <span className="truncate max-w-xs">{result.metadata.section}</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 rounded-lg">
                                            <ChartBarIcon className="h-4 w-4 text-emerald-400" />
                                            <span className="text-sm font-bold text-emerald-300">
                                                {(result.score * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                                        <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                                            {result.text}
                                        </p>
                                    </div>

                                    {result.metadata?.augmented && (
                                        <div className="mt-3 flex items-center justify-end space-x-1 text-xs text-indigo-400">
                                            <SparklesIcon className="w-4 h-4" />
                                            <span>Context Augmented</span>
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-center space-x-4 pt-8">
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                        disabled={currentPage === 1}
                                        className="btn-secondary disabled:opacity-30"
                                    >
                                        Previous
                                    </button>
                                    <span className="text-gray-400 font-medium">
                                        Page {currentPage} of {totalPages}
                                    </span>
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                        disabled={currentPage === totalPages}
                                        className="btn-secondary disabled:opacity-30"
                                    >
                                        Next
                                    </button>
                                </div>
                            )}
                        </>
                    )}

                    {/* No Results */}
                    {!loading && metrics && results.length === 0 && (
                        <div className="card text-center py-16">
                            <div className="w-20 h-20 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
                                <MagnifyingGlassIcon className="w-12 h-12 text-gray-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">No Results Found</h3>
                            <p className="text-gray-400 max-w-md mx-auto">
                                We couldn't find any relevant documents for your query. Try using different keywords or check your spelling.
                            </p>
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && !metrics && (
                        <div className="card text-center py-16 bg-gradient-to-br from-purple-500/10 to-cyan-500/10 border-purple-500/20">
                            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6 glow">
                                <LightBulbIcon className="w-12 h-12 text-white" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">Start Searching</h3>
                            <p className="text-gray-300 max-w-md mx-auto mb-6">
                                Enter a question or keywords above to search across your encrypted documents using AI-powered semantic search.
                            </p>
                            <div className="flex flex-wrap items-center justify-center gap-2">
                                <span className="text-sm text-gray-500">Try:</span>
                                {['What is...', 'How to...', 'Explain...'].map((example, i) => (
                                    <button
                                        key={i}
                                        onClick={() => setQuery(example)}
                                        className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition-all"
                                    >
                                        {example}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Search;
